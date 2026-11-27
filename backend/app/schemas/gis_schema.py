from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GISHealthResponse(BaseModel):
    status: str = "healthy"
    module: str = "GeoSense Phase 4 — Unified GIS & Spatial Mapping"
    database_backend: str
    postgis_schema_available: bool = True
    ne_india_states_loaded: bool = True


class GISLayerMetadata(BaseModel):
    layer_id: str
    layer_name: str
    layer_type: str
    source: str
    description: str
    crs: str = "EPSG:4326"
    geographic_coverage: str
    resolution: Optional[str] = None
    last_updated: str
    availability_status: str
    enabled: bool = True
    feature_count: int = 0


class GISLayersListResponse(BaseModel):
    count: int
    layers: List[GISLayerMetadata]


class GISFeatureCollectionResponse(BaseModel):
    type: str = "FeatureCollection"
    layer_id: str
    crs: str = "EPSG:4326"
    total_matched: int
    returned_count: int
    features: List[Dict[str, Any]]


class GISHotspotSummary(BaseModel):
    count: int
    methodology: str
    hotspots: List[Dict[str, Any]]


class GISLocationResponse(BaseModel):
    latitude: float
    longitude: float
    state: Optional[str] = None
    district_note: str
    dynamic_risk: Optional[Dict[str, Any]] = None
    susceptibility: Optional[Dict[str, Any]] = None
    satellite_detections: List[Dict[str, Any]] = Field(default_factory=list)
    incidents: List[Dict[str, Any]] = Field(default_factory=list)


class GISSummaryResponse(BaseModel):
    total_risk_assessments: int
    high_risk_locations: int
    critical_risk_locations: int
    available_detection_features: int
    available_susceptibility_analyses: int
    reported_incidents: int
    emergency_resources: int
    states_supported: List[str]
