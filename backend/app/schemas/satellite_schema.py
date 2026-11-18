from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status", json_schema_extra={"example": "healthy"})
    service: str = Field(..., description="Name of the service", json_schema_extra={"example": "GeoSense Satellite Detection API"})


class ModelStatusResponse(BaseModel):
    model_repository: str = Field(..., description="Hugging Face model repository identifier")
    status: str = Field(..., description="Model status: 'loaded', 'ready', 'downloading', 'not_loaded', 'failed'")
    device: str = Field(..., description="Compute device: 'cuda' or 'cpu'")
    model_version: Optional[str] = Field(None, description="Model revision or commit hash")
    checkpoint_path: Optional[str] = Field(None, description="Local path to model checkpoint")
    supported_input_formats: List[str] = Field(
        default=["GeoTIFF (.tif, .tiff)", "HDF5 (.h5)"],
        description="Supported satellite imagery container formats"
    )
    required_bands: List[str] = Field(
        default=["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"],
        description="Required satellite bands in exact order"
    )
    expected_dimensions: str = Field(
        default="224x224 (multispectral bands resized/resampled for Prithvi ViT)",
        description="Input dimensions expected by the model architecture"
    )
    error_details: Optional[str] = Field(None, description="Error details if model loading failed")


class DetectionStats(BaseModel):
    landslide_detected: bool = Field(..., description="Whether landslide pixels were detected")
    landslide_pixel_percentage: float = Field(..., description="Percentage of valid pixels classified as landslide")
    total_pixels: int = Field(..., description="Total count of valid pixels evaluated")
    landslide_pixels: int = Field(..., description="Count of pixels classified as landslide")


class GeospatialMetadata(BaseModel):
    has_georeference: bool = Field(..., description="Whether the input satellite image contained valid CRS and transform")
    crs: Optional[str] = Field(None, description="Coordinate Reference System (e.g. EPSG:4326)")
    bounds: Optional[Dict[str, float]] = Field(None, description="Bounding coordinates [left, bottom, right, top]")
    affine_transform: Optional[List[float]] = Field(None, description="Affine transform coefficients")


class DetectionFiles(BaseModel):
    original_image: str = Field(..., description="URL path to visual RGB representation of satellite image")
    segmentation_mask: str = Field(..., description="URL path to binary segmentation mask image")
    overlay: str = Field(..., description="URL path to visual colored overlay image")
    georeferenced_mask_tif: Optional[str] = Field(
        None, description="URL path to downloadable georeferenced GeoTIFF segmentation mask"
    )


class DetectionResponse(BaseModel):
    success: bool = Field(..., description="Whether detection completed successfully")
    result_id: str = Field(..., description="Unique identifier for the analysis result")
    model: str = Field(..., description="Model used for inference")
    detection: DetectionStats = Field(..., description="Statistical detection results")
    geospatial: GeospatialMetadata = Field(..., description="Geospatial metadata extracted from satellite input")
    files: DetectionFiles = Field(..., description="Generated result file routes")
    processing_time_seconds: float = Field(..., description="Inference and processing latency in seconds")


class ErrorResponse(BaseModel):
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(None, description="Detailed error information")
