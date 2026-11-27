import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.db.database import get_db_connection, ensure_phase9_schema
from app.services.notification_targeting_service import notification_targeting_service
from app.services.email_notification_service import email_notification_service
from app.services.fcm_service import fcm_service


class NotificationService:
    """
    Unified Notification & Delivery Tracking Service supporting ONLY:
    1. EMAIL (SMTP)
    2. FCM_PUSH (Firebase Cloud Messaging)
    Plus persistent in-app notification centre records. (No SMS.)
    """

    def dispatch_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        ensure_phase9_schema()
        recipients = notification_targeting_service.find_eligible_recipients(alert)
        now_iso = datetime.now(timezone.utc).isoformat()
        alert_id = alert["alert_id"]

        in_app_count = 0
        email_sent = email_failed = 0
        fcm_sent = fcm_failed = 0

        conn = get_db_connection()
        try:
            for rec in recipients:
                uid = rec["user_id"]
                # Prevent duplicate notification per alert + recipient
                existing_n = conn.execute(
                    "SELECT notification_id FROM notifications WHERE alert_id = ? AND recipient_user_id = ?",
                    (alert_id, uid),
                ).fetchone()
                if existing_n:
                    continue

                nid = f"notif_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO notifications (
                        notification_id, alert_id, recipient_user_id, recipient_role,
                        title, message, severity, is_read, is_acknowledged, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
                    """,
                    (
                        nid, alert_id, uid, rec["role"],
                        alert["title"], alert["description"], alert["severity"], now_iso,
                    ),
                )
                in_app_count += 1

                # Channel 1: EMAIL
                if rec["email_enabled"] and rec.get("email"):
                    e_res = email_notification_service.send_alert_email(
                        to_email=rec["email"], alert=alert, recipient_role=rec["role"]
                    )
                    conn.execute(
                        """
                        INSERT INTO notification_deliveries (
                            delivery_id, notification_id, alert_id, recipient_user_id,
                            channel, provider_message_id, delivery_status, provider_response,
                            attempt_count, error_message, sent_at
                        ) VALUES (?, ?, ?, ?, 'EMAIL', ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"del_{uuid.uuid4().hex[:12]}", nid, alert_id, uid,
                            e_res.get("provider_message_id"), e_res["delivery_status"],
                            e_res.get("provider_response"), e_res["attempt_count"],
                            e_res.get("error_message"), now_iso,
                        ),
                    )
                    if e_res["delivery_status"] == "SENT":
                        email_sent += 1
                    else:
                        email_failed += 1

                # Channel 2: FCM_PUSH
                if rec["push_enabled"] and rec.get("devices"):
                    for dev in rec["devices"]:
                        f_res = fcm_service.send_push(fcm_token=dev["fcm_token"], alert=alert)
                        conn.execute(
                            """
                            INSERT INTO notification_deliveries (
                                delivery_id, notification_id, alert_id, recipient_user_id,
                                channel, provider_message_id, delivery_status, provider_response,
                                attempt_count, error_message, sent_at
                            ) VALUES (?, ?, ?, ?, 'FCM_PUSH', ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                f"del_{uuid.uuid4().hex[:12]}", nid, alert_id, uid,
                                f_res.get("provider_message_id"), f_res["delivery_status"],
                                f_res.get("provider_response"), f_res["attempt_count"],
                                f_res.get("error_message"), now_iso,
                            ),
                        )
                        if f_res["delivery_status"] == "SENT":
                            fcm_sent += 1
                        else:
                            fcm_failed += 1

            conn.commit()
        finally:
            conn.close()

        return {
            "alert_id": alert_id,
            "recipients_targeted": len(recipients),
            "in_app_created": in_app_count,
            "email": {"sent": email_sent, "failed": email_failed},
            "fcm_push": {"sent": fcm_sent, "failed": fcm_failed},
        }

    def list_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            sql = (
                "SELECT n.*, a.alert_type, a.location_name, a.state, a.district, "
                "a.is_official_public_warning, a.expiry_at, a.source "
                "FROM notifications n JOIN alerts a ON n.alert_id = a.alert_id "
                "WHERE n.recipient_user_id = ? "
            )
            if unread_only:
                sql += "AND n.is_read = 0 "
            sql += "ORDER BY n.created_at DESC LIMIT 100"
            rows = conn.execute(sql, (user_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_read(self, notification_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        ensure_phase9_schema()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT * FROM notifications WHERE notification_id = ? AND recipient_user_id = ?",
                (notification_id, user_id),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE notifications SET is_read = 1, read_at = ? WHERE notification_id = ?",
                (now_iso, notification_id),
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM notifications WHERE notification_id = ?", (notification_id,)).fetchone())
        finally:
            conn.close()

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        ensure_phase9_schema()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE notifications SET is_acknowledged = 1, acknowledged_at = ?, is_read = 1, read_at = COALESCE(read_at, ?)
                WHERE alert_id = ? AND recipient_user_id = ?
                """,
                (now_iso, now_iso, alert_id, user_id),
            )
            conn.commit()
        finally:
            conn.close()
        return {"success": True, "alert_id": alert_id, "acknowledged_by": user_id, "acknowledged_at": now_iso}

    def register_device(self, user_id: str, fcm_token: str, platform: str = "android") -> Dict[str, Any]:
        ensure_phase9_schema()
        now_iso = datetime.now(timezone.utc).isoformat()
        did = f"dev_{uuid.uuid4().hex[:12]}"
        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT device_id FROM notification_devices WHERE user_id = ? AND fcm_token = ?",
                (user_id, fcm_token),
            ).fetchone()
            if existing:
                did = existing["device_id"]
                conn.execute(
                    "UPDATE notification_devices SET is_active = 1, platform = ?, updated_at = ? WHERE device_id = ?",
                    (platform, now_iso, did),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO notification_devices (device_id, user_id, fcm_token, platform, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    """,
                    (did, user_id, fcm_token, platform, now_iso, now_iso),
                )
            conn.commit()
        finally:
            conn.close()
        return {"device_id": did, "user_id": user_id, "platform": platform, "is_active": True}

    def unregister_device(self, device_id: str, user_id: str) -> bool:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            cur = conn.execute(
                "DELETE FROM notification_devices WHERE device_id = ? AND user_id = ?",
                (device_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def update_preferences(self, user_id: str, prefs: Dict[str, Any]) -> Dict[str, Any]:
        ensure_phase9_schema()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            existing = conn.execute("SELECT * FROM notification_preferences WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                cur = dict(existing)
                email_en = int(prefs["email_enabled"]) if prefs.get("email_enabled") is not None else cur["email_enabled"]
                push_en = int(prefs["push_enabled"]) if prefs.get("push_enabled") is not None else cur["push_enabled"]
                st = prefs.get("preferred_state") if prefs.get("preferred_state") is not None else cur["preferred_state"]
                dist = prefs.get("preferred_district") if prefs.get("preferred_district") is not None else cur["preferred_district"]
                lat = prefs.get("latitude") if prefs.get("latitude") is not None else cur["latitude"]
                lon = prefs.get("longitude") if prefs.get("longitude") is not None else cur["longitude"]
                conn.execute(
                    """
                    UPDATE notification_preferences
                    SET email_enabled=?, push_enabled=?, preferred_state=?, preferred_district=?, latitude=?, longitude=?, updated_at=?
                    WHERE user_id=?
                    """,
                    (email_en, push_en, st, dist, lat, lon, now_iso, user_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO notification_preferences (
                        user_id, email_enabled, push_enabled, preferred_state, preferred_district, latitude, longitude, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        int(prefs["email_enabled"]) if prefs.get("email_enabled") is not None else 1,
                        int(prefs["push_enabled"]) if prefs.get("push_enabled") is not None else 1,
                        prefs.get("preferred_state"),
                        prefs.get("preferred_district"),
                        prefs.get("latitude"),
                        prefs.get("longitude"),
                        now_iso,
                    ),
                )
            conn.commit()
            return dict(conn.execute("SELECT * FROM notification_preferences WHERE user_id = ?", (user_id,)).fetchone())
        finally:
            conn.close()

    def get_alert_deliveries(self, alert_id: str) -> List[Dict[str, Any]]:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM notification_deliveries WHERE alert_id = ? ORDER BY sent_at DESC",
                (alert_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


notification_service = NotificationService()
