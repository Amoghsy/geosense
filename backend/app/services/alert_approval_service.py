from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from app.db.database import get_db_connection, ensure_phase9_schema
from app.services.auth_service import log_audit_event
from app.services.notification_service import notification_service


class AlertApprovalService:
    """
    Authority-controlled alert approval, rejection, publication, and cancellation workflow.
    Only AUTHORITY or ADMIN roles may approve/publish official warnings.
    """

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_alerts(
        self,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        approval_status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        ensure_phase9_schema()
        clauses = []
        params: List[Any] = []
        if severity:
            clauses.append("severity = ?")
            params.append(severity.upper())
        if alert_type:
            clauses.append("alert_type = ?")
            params.append(alert_type.upper())
        if state:
            clauses.append("LOWER(state) = ?")
            params.append(state.strip().lower())
        if district:
            clauses.append("LOWER(district) = ?")
            params.append(district.strip().lower())
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status.upper())
        if start_date:
            clauses.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("created_at <= ?")
            params.append(end_date)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                f"SELECT * FROM alerts {where_sql} ORDER BY created_at DESC LIMIT ?",
                tuple(params + [limit]),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def approve_alert(
        self,
        alert_id: str,
        authority_user: Dict[str, Any],
        admin_notes: Optional[str] = None,
        expiry_hours: int = 24,
    ) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        expiry_iso = (now_dt + timedelta(hours=expiry_hours)).isoformat()

        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE alerts
                SET approval_status = 'APPROVED', approving_authority = ?, admin_notes = ?,
                    expiry_at = ?, updated_at = ?
                WHERE alert_id = ?
                """,
                (authority_user["user_id"], admin_notes, expiry_iso, now_iso, alert_id),
            )
            conn.commit()
        finally:
            conn.close()

        log_audit_event(authority_user["user_id"], authority_user["role"], "ALERT_APPROVED", "alert", alert_id, {"notes": admin_notes})
        return self.get_alert(alert_id)

    def reject_alert(
        self,
        alert_id: str,
        authority_user: Dict[str, Any],
        admin_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE alerts
                SET approval_status = 'REJECTED', approving_authority = ?, admin_notes = ?, updated_at = ?
                WHERE alert_id = ?
                """,
                (authority_user["user_id"], admin_notes, now_iso, alert_id),
            )
            conn.commit()
        finally:
            conn.close()

        log_audit_event(authority_user["user_id"], authority_user["role"], "ALERT_REJECTED", "alert", alert_id, {"notes": admin_notes})
        return self.get_alert(alert_id)

    def publish_alert(
        self,
        alert_id: str,
        authority_user: Dict[str, Any],
        admin_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        if alert["approval_status"] not in {"APPROVED", "PENDING_REVIEW"}:
            raise ValueError(f"Cannot publish alert in status '{alert['approval_status']}'.")

        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE alerts
                SET approval_status = 'PUBLISHED', approving_authority = COALESCE(approving_authority, ?),
                    admin_notes = COALESCE(?, admin_notes), is_official_public_warning = 1,
                    published_at = ?, updated_at = ?
                WHERE alert_id = ?
                """,
                (authority_user["user_id"], admin_notes, now_iso, now_iso, alert_id),
            )
            conn.commit()
        finally:
            conn.close()

        updated = self.get_alert(alert_id)
        delivery_summary = notification_service.dispatch_alert(updated)
        log_audit_event(
            authority_user["user_id"], authority_user["role"], "ALERT_PUBLISHED", "alert", alert_id,
            {"delivery_summary": delivery_summary},
        )
        return {"alert": updated, "delivery_summary": delivery_summary}

    def cancel_alert(
        self,
        alert_id: str,
        authority_user: Dict[str, Any],
        admin_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE alerts SET approval_status = 'CANCELLED', admin_notes = ?, updated_at = ? WHERE alert_id = ?",
                (admin_notes, now_iso, alert_id),
            )
            conn.commit()
        finally:
            conn.close()
        log_audit_event(authority_user["user_id"], authority_user["role"], "ALERT_CANCELLED", "alert", alert_id, {"notes": admin_notes})
        return self.get_alert(alert_id)


alert_approval_service = AlertApprovalService()
