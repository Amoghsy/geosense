from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

AlertType = Literal[
    "RISK_ESCALATION",
    "HEAVY_RAINFALL",
    "LANDSLIDE_DETECTION",
    "VERIFIED_INCIDENT",
    "HOTSPOT_WARNING",
    "OFFICIAL_ADVISORY",
]
AlertSeverity = Literal["INFORMATION", "ADVISORY", "WARNING", "CRITICAL"]
ApprovalStatus = Literal[
    "GENERATED", "PENDING_REVIEW", "APPROVED", "REJECTED", "PUBLISHED", "EXPIRED", "CANCELLED"
]


class AlertGenerateRequest(BaseModel):
    assessment_id: Optional[str] = None
    incident_id: Optional[str] = None
    location_id: Optional[str] = None
    state: Optional[str] = None


class AlertDecisionRequest(BaseModel):
    admin_notes: Optional[str] = None
    expiry_hours: Optional[int] = Field(24, ge=1, le=720)


class DeviceRegisterRequest(BaseModel):
    fcm_token: str = Field(..., min_length=10, max_length=512)
    platform: Literal["android", "ios", "web"] = "android"


class NotificationPreferenceRequest(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    preferred_state: Optional[str] = None
    preferred_district: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
