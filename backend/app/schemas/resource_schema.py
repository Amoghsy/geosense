from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

ResourceCategory = Literal[
    "HOSPITAL",
    "HEALTH_CENTRE",
    "AMBULANCE",
    "SHELTER",
    "RESCUE_TEAM",
    "FIRE_STATION",
    "POLICE_STATION",
    "RELIEF_CENTRE",
    "HEAVY_EQUIPMENT",
]

VerificationStatus = Literal["PENDING", "VERIFIED", "REJECTED"]
OperationalStatus = Literal["OPERATIONAL", "TEMPORARILY_UNAVAILABLE", "CLOSED", "UNKNOWN"]
AvailabilityStatus = Literal["AVAILABLE", "LIMITED", "FULL", "UNAVAILABLE", "UNKNOWN"]


class ResourceCreateRequest(BaseModel):
    resource_name: str = Field(..., min_length=2, max_length=200)
    resource_type: ResourceCategory
    description: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    contact_number: Optional[str] = None
    is_public_contact: bool = False
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)
    source: Optional[str] = "Authority / Field Submission"


class ResourceUpdateRequest(BaseModel):
    resource_name: Optional[str] = Field(None, min_length=2, max_length=200)
    resource_type: Optional[ResourceCategory] = None
    description: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    contact_number: Optional[str] = None
    is_public_contact: Optional[bool] = None
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)


class ResourceVerifyRequest(BaseModel):
    verification_status: Literal["VERIFIED", "REJECTED"]
    operational_status: Optional[OperationalStatus] = None
    availability_status: Optional[AvailabilityStatus] = None
    notes: Optional[str] = None


class ResourceAvailabilityUpdateRequest(BaseModel):
    operational_status: Optional[OperationalStatus] = None
    availability_status: Optional[AvailabilityStatus] = None
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class ResourceResponse(BaseModel):
    resource_id: str
    resource_name: str
    resource_type: str
    description: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: float
    longitude: float
    contact_number: Optional[str] = None
    is_public_contact: bool = False
    capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    remaining_capacity: Optional[int] = None
    availability_status: str
    operational_status: str
    verification_status: str
    source: str
    last_verified_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    distance_km: Optional[float] = None
    distance_note: Optional[str] = None


class ResourceListResponse(BaseModel):
    count: int
    total_matched: int
    resources: List[ResourceResponse]


class ResourceNearbyResponse(BaseModel):
    latitude: float
    longitude: float
    radius_km: float
    distance_type: str = "straight_line_haversine_km"
    distance_disclaimer: str = (
        "Straight-line geographic distance only; does not represent road travel distance or travel time."
    )
    count: int
    resources: List[ResourceResponse]


class ResourceStatsResponse(BaseModel):
    total_resources: int
    verified_resources: int
    pending_verification: int
    rejected_resources: int
    operational_resources: int
    temporarily_unavailable: int
    full_shelters: int
    by_category: Dict[str, int]


class ResourceRecommendationResponse(BaseModel):
    latitude: float
    longitude: float
    radius_km: float
    count: int
    advisory_disclaimer: str
    recommendations: List[Dict[str, Any]]
