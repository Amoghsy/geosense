from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.alert_schema import (
    AlertGenerateRequest,
    AlertDecisionRequest,
    DeviceRegisterRequest,
    NotificationPreferenceRequest,
)
from app.services.auth_service import get_current_user, require_roles
from app.services.alert_generation_service import alert_generation_service
from app.services.alert_approval_service import alert_approval_service
from app.services.notification_service import notification_service
from app.services.email_notification_service import email_notification_service
from app.services.fcm_service import fcm_service

router = APIRouter(tags=["Phase 9 — Alerts & Notifications (Email + FCM)"])


@router.get("/alerts/status", summary="Email & FCM Notification Channel Status")
async def notification_channel_status():
    return {
        "email_smtp_configured": email_notification_service.is_configured(),
        "fcm_configured": fcm_service.is_configured(),
        "supported_channels": ["EMAIL", "FCM_PUSH"],
    }


@router.post("/alerts/generate", status_code=status.HTTP_201_CREATED, summary="Generate Alert Recommendations")
async def generate_alerts(
    req: AlertGenerateRequest,
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    generated = []
    if req.assessment_id:
        generated.extend(alert_generation_service.evaluate_risk_assessment(req.assessment_id))
    if req.incident_id:
        generated.extend(alert_generation_service.evaluate_verified_incident(req.incident_id))
    return {"count": len(generated), "alerts": generated}


@router.get("/alerts", summary="List Alerts with Filters")
async def list_alerts(
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    eff_status = "PUBLISHED" if user["role"] == "CITIZEN" else approval_status
    items = alert_approval_service.list_alerts(
        severity=severity,
        alert_type=alert_type,
        state=state,
        district=district,
        approval_status=eff_status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return {"count": len(items), "alerts": items}


@router.get("/alerts/{alert_id}", summary="Get Alert Details")
async def get_alert(alert_id: str, user: dict = Depends(get_current_user)):
    alert = alert_approval_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    if user["role"] == "CITIZEN" and alert["approval_status"] != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unpublished alerts are restricted.")
    return alert


@router.post("/alerts/{alert_id}/approve", summary="Approve Alert (Authority Only)")
async def approve_alert(
    alert_id: str,
    req: AlertDecisionRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    res = alert_approval_service.approve_alert(
        alert_id, user, admin_notes=req.admin_notes, expiry_hours=req.expiry_hours or 24
    )
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return res


@router.post("/alerts/{alert_id}/reject", summary="Reject Alert (Authority Only)")
async def reject_alert(
    alert_id: str,
    req: AlertDecisionRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    res = alert_approval_service.reject_alert(alert_id, user, admin_notes=req.admin_notes)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return res


@router.post("/alerts/{alert_id}/publish", summary="Publish Approved Alert via Email & FCM (Authority Only)")
async def publish_alert(
    alert_id: str,
    req: AlertDecisionRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    try:
        res = alert_approval_service.publish_alert(alert_id, user, admin_notes=req.admin_notes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return res


@router.post("/alerts/{alert_id}/cancel", summary="Cancel Alert (Authority Only)")
async def cancel_alert(
    alert_id: str,
    req: AlertDecisionRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    res = alert_approval_service.cancel_alert(alert_id, user, admin_notes=req.admin_notes)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return res


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge Alert")
async def acknowledge_alert(alert_id: str, user: dict = Depends(get_current_user)):
    return notification_service.acknowledge_alert(alert_id, user["user_id"])


@router.get("/alerts/{alert_id}/deliveries", summary="View Email & FCM Delivery History")
async def get_alert_deliveries(
    alert_id: str,
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    deliveries = notification_service.get_alert_deliveries(alert_id)
    return {"alert_id": alert_id, "count": len(deliveries), "deliveries": deliveries}


@router.get("/notifications", summary="List User In-App Notifications")
async def get_my_notifications(
    unread_only: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    items = notification_service.list_user_notifications(user["user_id"], unread_only=unread_only)
    return {"count": len(items), "notifications": items}


@router.patch("/notifications/{notification_id}/read", summary="Mark Notification as Read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    res = notification_service.mark_read(notification_id, user["user_id"])
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return res


@router.post("/notifications/devices/register", summary="Register FCM Device Token")
async def register_fcm_device(req: DeviceRegisterRequest, user: dict = Depends(get_current_user)):
    return notification_service.register_device(user["user_id"], req.fcm_token, req.platform)


@router.delete("/notifications/devices/{device_id}", summary="Unregister FCM Device Token")
async def unregister_fcm_device(device_id: str, user: dict = Depends(get_current_user)):
    ok = notification_service.unregister_device(device_id, user["user_id"])
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    return {"success": True, "device_id": device_id}


@router.patch("/notifications/preferences", summary="Update Email & Push Notification Preferences")
async def update_notification_preferences(
    req: NotificationPreferenceRequest,
    user: dict = Depends(get_current_user),
):
    return notification_service.update_preferences(user["user_id"], req.model_dump(exclude_none=True))
