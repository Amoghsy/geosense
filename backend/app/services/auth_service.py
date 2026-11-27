import os
import hmac
import hashlib
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.database import get_db_connection, ensure_phase8_schema

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "geosense-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
ADMIN_PROVISION_SECRET = os.getenv("ADMIN_PROVISION_SECRET", "geosense-admin-provision")

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return f"{salt}${dk}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def create_access_token(user: Dict[str, Any], expires_minutes: int = JWT_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "role": user["role"],
        "assigned_state": user.get("assigned_state"),
        "assigned_district": user.get("assigned_district"),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from exc


def log_audit_event(
    actor_user_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str,
    details: Dict[str, Any],
) -> None:
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO audit_logs (
                log_id, actor_user_id, actor_role, action, target_type, target_id, details_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"aud_{uuid.uuid4().hex[:12]}",
                actor_user_id,
                actor_role,
                action,
                target_type,
                target_id,
                json.dumps(details),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d.pop("password_hash", None)
        return d
    finally:
        conn.close()


def register_user(
    email: str,
    password: str,
    full_name: str,
    phone: Optional[str] = None,
    role: str = "CITIZEN",
    assigned_state: Optional[str] = None,
    assigned_district: Optional[str] = None,
    provision_secret: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_phase8_schema()
    norm_role = role.upper()
    if norm_role not in {"CITIZEN", "FIELD_OFFICER", "AUTHORITY", "ADMIN"}:
        raise ValueError(f"Unsupported role: {role}")

    if norm_role != "CITIZEN" and provision_secret != ADMIN_PROVISION_SECRET:
        raise PermissionError("Privileged roles (FIELD_OFFICER, AUTHORITY, ADMIN) require valid provisioning authorization.")

    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT user_id FROM users WHERE LOWER(email) = ?", (email.strip().lower(),)).fetchone()
        if existing:
            raise ValueError("An account with this email already exists.")

        uid = f"usr_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO users (
                user_id, email, password_hash, full_name, phone, role,
                assigned_state, assigned_district, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                uid,
                email.strip().lower(),
                hash_password(password),
                full_name.strip(),
                phone,
                norm_role,
                assigned_state,
                assigned_district,
                now_iso,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return get_user_by_id(uid)


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    ensure_phase8_schema()
    identifier = email.strip().lower()
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM users
            WHERE LOWER(email) = ?
               OR LOWER(COALESCE(officer_code, '')) = ?
               OR LOWER(REPLACE(COALESCE(phone, ''), ' ', '')) = ?
            """,
            (identifier, identifier, identifier.replace(" ", "")),
        ).fetchone()
        if not row or not row["is_active"]:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        d = dict(row)
        d.pop("password_hash", None)
        return d
    finally:
        conn.close()


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token.",
        )
    payload = decode_access_token(creds.credentials)
    user = get_user_by_id(payload["sub"])
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
        )
    return user


def require_roles(*allowed_roles: str):
    allowed = {r.upper() for r in allowed_roles}

    async def _checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"].upper() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{user['role']}'. Required: {sorted(allowed)}",
            )
        return user

    return _checker
