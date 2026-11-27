from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

UserRole = Literal["citizen", "field_officer", "authority"]


class AgentLocationContext(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    region_id: Optional[str] = None


class AgentCreateSessionRequest(BaseModel):
    role: UserRole = "citizen"
    user_id: Optional[str] = None
    location_context: Optional[AgentLocationContext] = None


class AgentSessionResponse(BaseModel):
    session_id: str
    role: UserRole
    user_id: Optional[str] = None
    location_context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    role: UserRole = "citizen"
    user_id: Optional[str] = None
    location_context: Optional[AgentLocationContext] = None


class AgentChatResponse(BaseModel):
    success: bool = True
    session_id: str
    role: UserRole
    execution_mode: str
    reply: str
    tools_used: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    timestamps: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class SituationReportRequest(BaseModel):
    region_id: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    role: UserRole = "authority"


class AgentHealthResponse(BaseModel):
    status: str = "healthy"
    module: str = "GeoSense Phase 6 — AI Decision-Support Agent"
    google_adk_installed: bool
    gemini_api_key_configured: bool
    active_execution_mode: str
    available_tools: List[str]
