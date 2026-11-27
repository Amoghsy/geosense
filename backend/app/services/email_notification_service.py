import os
import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Tuple

logger = logging.getLogger("geosense.email_service")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailNotificationService:
    """
    Modular SMTP Email Notification Service.
    Reads configuration strictly from environment variables (never hardcoded secrets).
    Distinguishes SENT (accepted by SMTP server) from DELIVERED (never falsely claimed).
    """

    def is_configured(self) -> bool:
        return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM_EMAIL"))

    def validate_email(self, addr: str) -> bool:
        return bool(addr and EMAIL_REGEX.match(addr.strip()))

    def render_template(self, alert: Dict[str, Any], recipient_role: str) -> Tuple[str, str, str]:
        sev = alert.get("severity", "ADVISORY")
        title = alert.get("title", "GeoSense Alert")
        loc = alert.get("location_name") or alert.get("location_id") or "North Eastern India"
        state = alert.get("state") or "N/A"
        district = alert.get("district") or "N/A"
        desc = alert.get("description", "")
        issued = alert.get("published_at") or alert.get("created_at") or "N/A"
        expiry = alert.get("expiry_at") or "Not specified"
        source = alert.get("source", "GeoSense Early-Warning System")

        role_upper = recipient_role.upper()
        if role_upper == "CITIZEN":
            role_note = "Public Safety Advisory: Follow official NDMA/SDMA instructions and avoid unstable slopes."
        elif role_upper == "FIELD_OFFICER":
            role_note = "Field Officer Action: Review assigned corridor, verify conditions on site, and acknowledge in GeoSense."
        else:
            role_note = "Authority Briefing: Review delivery logs and coordinate district response resources as required."

        subject = f"[GeoSense {sev}] {title} — {loc}"
        text_body = (
            f"{subject}\n\n"
            f"Severity: {sev}\nLocation: {loc} ({district}, {state})\n"
            f"Issued: {issued}\nExpires: {expiry}\nSource: {source}\n\n"
            f"{desc}\n\n{role_note}\n"
            "View full details in the GeoSense application."
        )
        html_body = (
            f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #cbd5e1;border-radius:8px;padding:16px;'>"
            f"<h2 style='color:#0f172a;margin-top:0;'>GeoSense {sev}: {title}</h2>"
            f"<p><strong>Location:</strong> {loc} ({district}, {state})<br>"
            f"<strong>Issued:</strong> {issued}<br><strong>Expires:</strong> {expiry}<br>"
            f"<strong>Source:</strong> {source}</p>"
            f"<p style='background:#f8fafc;padding:12px;border-radius:6px;'>{desc}</p>"
            f"<p style='color:#334155;font-size:13px;'>{role_note}</p>"
            f"</div>"
        )
        return subject, text_body, html_body

    def send_alert_email(
        self,
        to_email: str,
        alert: Dict[str, Any],
        recipient_role: str = "CITIZEN",
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        if not self.validate_email(to_email):
            return {
                "delivery_status": "FAILED",
                "attempt_count": 1,
                "error_message": f"Invalid recipient email address: {to_email}",
                "provider_message_id": None,
                "provider_response": None,
            }

        if not self.is_configured():
            return {
                "delivery_status": "FAILED",
                "attempt_count": 1,
                "error_message": "SMTP service not configured (SMTP_HOST / SMTP_FROM_EMAIL missing).",
                "provider_message_id": None,
                "provider_response": "SMTP_UNCONFIGURED",
            }

        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME", "")
        password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("SMTP_FROM_EMAIL", "")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        subject, text_body, html_body = self.render_template(alert, recipient_role)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                with smtplib.SMTP(host, port, timeout=15) as server:
                    if use_tls:
                        server.starttls()
                    if username and password:
                        server.login(username, password)
                    server.sendmail(from_email, [to_email], msg.as_string())
                return {
                    "delivery_status": "SENT",
                    "attempt_count": attempt,
                    "provider_message_id": msg.get("Message-ID") or f"smtp_{alert['alert_id']}",
                    "provider_response": "Accepted by SMTP server (delivery to inbox not guaranteed)",
                    "error_message": None,
                }
            except Exception as exc:
                last_err = str(exc)
                logger.warning(f"SMTP attempt {attempt} failed for {to_email}: {exc}")

        return {
            "delivery_status": "FAILED",
            "attempt_count": max_retries,
            "provider_message_id": None,
            "provider_response": None,
            "error_message": last_err,
        }


email_notification_service = EmailNotificationService()
