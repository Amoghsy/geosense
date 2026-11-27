import os
import logging
from typing import Dict, Any, Optional

from app.db.database import get_db_connection

logger = logging.getLogger("geosense.fcm_service")

try:
    import firebase_admin  # type: ignore
    from firebase_admin import credentials, messaging  # type: ignore
    FIREBASE_SDK_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None
    FIREBASE_SDK_AVAILABLE = False


class FCMService:
    """
    Firebase Cloud Messaging (FCM) push notification service via Firebase Admin SDK.
    Handles unconfigured credentials gracefully, deactivates invalid/expired tokens,
    and distinguishes SENT (accepted by Firebase) from DELIVERED.
    """

    def __init__(self):
        self._initialized = False

    def _build_inline_credentials_dict(self) -> Optional[Dict[str, Any]]:
        project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
        private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
        if not (project_id and client_email and private_key):
            return None
        return {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": project_id,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": client_email,
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv(
                "FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL", ""),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com"),
        }

    def is_configured(self) -> bool:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        has_file = bool(cred_path and os.path.isfile(cred_path))
        has_inline = self._build_inline_credentials_dict() is not None
        return bool(FIREBASE_SDK_AVAILABLE and (has_file or has_inline))

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        if not self.is_configured():
            return False
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        try:
            if not firebase_admin._apps:
                if cred_path and os.path.isfile(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    cred = credentials.Certificate(self._build_inline_credentials_dict())
                firebase_admin.initialize_app(cred)
            self._initialized = True
            return True
        except Exception as exc:
            logger.error(f"Failed to initialize Firebase Admin SDK: {exc}")
            return False

    def deactivate_token(self, fcm_token: str) -> None:
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE notification_devices SET is_active = 0 WHERE fcm_token = ?",
                (fcm_token,),
            )
            conn.commit()
        finally:
            conn.close()

    def send_push(
        self,
        fcm_token: str,
        alert: Dict[str, Any],
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        if not FIREBASE_SDK_AVAILABLE:
            return {
                "delivery_status": "FAILED",
                "attempt_count": 1,
                "provider_message_id": None,
                "provider_response": "FIREBASE_ADMIN_NOT_INSTALLED",
                "error_message": "firebase-admin package is not installed.",
            }

        if not self._ensure_initialized():
            return {
                "delivery_status": "FAILED",
                "attempt_count": 1,
                "provider_message_id": None,
                "provider_response": "FIREBASE_CREDENTIALS_UNCONFIGURED",
                "error_message": "FIREBASE_CREDENTIALS_PATH / GOOGLE_APPLICATION_CREDENTIALS not configured.",
            }

        msg = messaging.Message(
            notification=messaging.Notification(
                title=f"[{alert.get('severity', 'ADVISORY')}] {alert.get('title', 'GeoSense Alert')}",
                body=(alert.get("description") or "")[:180],
            ),
            data={
                "alert_id": str(alert.get("alert_id", "")),
                "severity": str(alert.get("severity", "")),
                "alert_type": str(alert.get("alert_type", "")),
                "location_name": str(alert.get("location_name") or ""),
                "timestamp": str(alert.get("published_at") or alert.get("created_at") or ""),
            },
            token=fcm_token,
        )

        last_err: Optional[str] = None
        for attempt in range(1, max_retries + 1):
            try:
                msg_id = messaging.send(msg)
                return {
                    "delivery_status": "SENT",
                    "attempt_count": attempt,
                    "provider_message_id": msg_id,
                    "provider_response": "Accepted by FCM (does not confirm device display)",
                    "error_message": None,
                }
            except Exception as exc:
                last_err = str(exc)
                err_l = last_err.lower()
                if "unregistered" in err_l or "invalid-registration-token" in err_l or "not-found" in err_l:
                    self.deactivate_token(fcm_token)
                    return {
                        "delivery_status": "FAILED",
                        "attempt_count": attempt,
                        "provider_message_id": None,
                        "provider_response": "INVALID_OR_EXPIRED_TOKEN",
                        "error_message": last_err,
                    }
                logger.warning(f"FCM send attempt {attempt} failed: {exc}")

        return {
            "delivery_status": "FAILED",
            "attempt_count": max_retries,
            "provider_message_id": None,
            "provider_response": None,
            "error_message": last_err,
        }


fcm_service = FCMService()
