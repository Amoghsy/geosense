from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SusceptibilityHealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    module: str = Field("GeoSense Phase 2 — Multimodal Landslide Susceptibility Analysis")
    model_loaded: bool = Field(...)


class SusceptibilityModelStatusResponse(BaseModel):
    model_repository: str
    model_revision: str
    status: str = Field(..., description="'ready', 'not_loaded', or 'failed'")
    device: str = Field(..., description="'cpu' or 'cuda'")
    checkpoint_path: Optional[str] = None
    supported_inputs: List[str]
    required_channels: List[str]
    expected_patch_size: str
    actual_task: str
    error_details: Optional[str] = None


class SusceptibilityModelInfoResponse(BaseModel):
    model_repository: str
    model_revision: str
    license: str
    architecture: Dict[str, Any]
    actual_task: str
    supported_input_formats: List[str]
    required_channels: List[str]
    preprocessing_requirements: Dict[str, Any]
    output_format: Dict[str, Any]
    evaluation_metrics: Dict[str, Any]
    geographic_coverage_and_limitations: Dict[str, Any]


class SusceptibilityPredictionOutput(BaseModel):
    raw_logit: float = Field(..., description="Raw scalar logit output from Fusion Head")
    susceptibility_score: float = Field(..., description="Sigmoid-activated score in [0.0, 1.0]")
    decision_threshold: float = Field(0.291, description="Documented optimal threshold from Precision-Recall validation")
    is_susceptible: bool = Field(..., description="True if susceptibility_score >= 0.291")
    susceptibility_class: str = Field(..., description="Documented binary susceptibility label ('Susceptible' or 'Non-Susceptible')")
    tile_count: int = Field(1, description="Number of 224x224 patches evaluated")
    tile_scores: Optional[List[Dict[str, Any]]] = Field(None, description="Per-tile scores when tiled over a larger raster")


class SusceptibilityGeographicMetadata(BaseModel):
    region_id: Optional[str] = None
    region_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_georeference: bool = False
    crs: Optional[str] = None
    bounds: Optional[Dict[str, float]] = None
    image_dimensions: Dict[str, int]
    coverage_status: str = Field(..., description="Validation status of geographic coverage for NE India")
    coverage_limitations: str


class SusceptibilityFiles(BaseModel):
    rgb_preview: str
    terrain_preview: str
    geojson_map: Optional[str] = None
    metadata_json: str


class SusceptibilityAnalysisResponse(BaseModel):
    success: bool = True
    analysis_id: str
    model_repository: str
    model_revision: str
    prediction: SusceptibilityPredictionOutput
    geographic: SusceptibilityGeographicMetadata
    input_metadata: Dict[str, Any]
    source_metadata: Dict[str, Any]
    data_quality_warnings: List[str] = Field(default_factory=list)
    files: SusceptibilityFiles
    processing_time_seconds: float
    created_at: str
