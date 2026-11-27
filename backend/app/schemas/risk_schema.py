from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WeatherCurrentResponse(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    precipitation_mm: Optional[float] = None
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_code: Optional[int] = None
    weather_condition: str
    observation_time: Optional[str] = None
    retrieved_at: str
    is_stale: bool = False
    cached: bool = False
    source: str = "Open-Meteo Forecast API"
    warnings: List[str] = Field(default_factory=list)


class RollingWindowStat(BaseModel):
    window: str
    rainfall_mm: Optional[float] = None
    valid_hours: int
    expected_hours: int
    is_complete: bool
    contains_forecast: bool = False


class RainfallIndicatorsResponse(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    observed_windows: Dict[str, RollingWindowStat]
    forecast_windows: Dict[str, RollingWindowStat]
    intensity: Dict[str, Optional[float]]
    awi_proxy: Dict[str, Any]
    rainfall_concern_score: Optional[float] = None
    observed_rainfall_score: Optional[float] = None
    forecast_rainfall_score: Optional[float] = None
    data_completeness: float
    calculated_at: str
    warnings: List[str] = Field(default_factory=list)
    calibration_note: str


class RiskAnalyzeRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_id: Optional[str] = Field(None, description="Optional identifier; defaults to grid coordinate key")
    location_name: Optional[str] = Field(None, description="Optional village/town/district name")
    region_id: Optional[str] = Field(None, description="Optional NE India state key")
    phase1_result_id: Optional[str] = Field(None, description="Optional Phase 1 Prithvi detection ID")
    phase2_analysis_id: Optional[str] = Field(None, description="Optional Phase 2 susceptibility analysis ID")
    elevation_m: Optional[float] = Field(None, description="Optional verified elevation in metres")
    slope_deg: Optional[float] = Field(None, ge=0.0, le=90.0, description="Optional verified slope in degrees")
    soil_moisture_m3_m3: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional actual sensor soil moisture")


class RiskAssessmentResponse(BaseModel):
    success: bool = True
    assessment_id: str
    location_id: str
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    risk_score: Optional[float] = Field(None, description="Heuristic risk index 0-100 (NOT a calibrated probability)")
    risk_category: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL, or INSUFFICIENT_DATA")
    is_calibrated_probability: bool = False
    factor_scores: Dict[str, Optional[float]]
    factor_weights_configured: Dict[str, float]
    factor_weights_effective: Dict[str, float]
    missing_factors: List[str]
    completeness_score: float
    rainfall_indicators: Optional[Dict[str, Any]] = None
    susceptibility_info: Optional[Dict[str, Any]] = None
    terrain_info: Optional[Dict[str, Any]] = None
    satellite_detection_evidence: Optional[Dict[str, Any]] = None
    explanation: str
    data_freshness: Dict[str, Any]
    data_sources: List[str]
    warnings: List[str] = Field(default_factory=list)
    assessment_time: str


class RiskExplanationResponse(BaseModel):
    assessment_id: str
    location_id: str
    risk_score: Optional[float]
    risk_category: str
    explanation: str
    factor_scores: Dict[str, Optional[float]]
    factor_weights_effective: Dict[str, float]
    missing_factors: List[str]
    data_freshness: Dict[str, Any]
    assessment_time: str


class RiskHistoryResponse(BaseModel):
    location_id: str
    count: int
    assessments: List[Dict[str, Any]]


class RiskHotspotsResponse(BaseModel):
    count: int
    categories_included: List[str]
    hotspots: List[Dict[str, Any]]
