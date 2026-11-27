from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

SystemRole = Literal["CITIZEN", "FIELD_OFFICER", "AUTHORITY", "ADMIN"]
IncidentCategory = Literal[
    "LANDSLIDE", "ROAD_BLOCKAGE", "SLOPE_CRACKS", "FALLING_ROCKS",
    "FLOODING", "DAMAGED_INFRASTRUCTURE", "OTHER"
]
InspectionStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "NEEDS_FOLLOW_UP"]


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=4, max_length=150)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = None
    role: SystemRole = "CITIZEN"
    assigned_state: Optional[str] = None
    assigned_district: Optional[str] = None
    provision_secret: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = None


class IncidentCreateRequest(BaseModel):
    incident_category: IncidentCategory = "LANDSLIDE"
    description: str = Field(..., min_length=5, max_length=2000)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    incident_time: Optional[str] = None
    contact_info: Optional[str] = None


class IncidentVerifyRequest(BaseModel):
    status: Literal["VERIFIED", "REJECTED", "NEEDS_INFO"]
    verification_notes: Optional[str] = None


class IncidentAssignRequest(BaseModel):
    officer_id: str
    notes: Optional[str] = None


class InspectionCreateRequest(BaseModel):
    location_id: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    status: InspectionStatus = "IN_PROGRESS"
    observations: str = Field(..., min_length=3, max_length=2000)
    inspection_notes: Optional[str] = None
    follow_up_required: bool = False


class InspectionUpdateRequest(BaseModel):
    status: Optional[InspectionStatus] = None
    observations: Optional[str] = None
    inspection_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
