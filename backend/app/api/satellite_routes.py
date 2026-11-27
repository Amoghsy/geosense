import os
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from app.schemas.satellite_schema import (
    HealthResponse,
    ModelStatusResponse,
    DetectionResponse,
    ErrorResponse
)
from app.ml.model_loader import get_model_manager, ModelLoadingError
from app.ml.preprocessing import SatelliteValidationError
from app.services.satellite_service import satellite_service

router = APIRouter()


# ==========================================
# Health & Status Endpoints
# ==========================================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Returns the operational status of the GeoSense Satellite Landslide Detection service."
)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="GeoSense Satellite Detection API"
    )


@router.get(
    "/model/status",
    response_model=ModelStatusResponse,
    tags=["Model"],
    summary="Model Status",
    description="Returns the status of the Hugging Face Prithvi Landslide foundation model, device type (CPU/GPU), and input requirements."
)
async def get_model_status():
    manager = get_model_manager()
    status_dict = manager.get_status_info()
    return ModelStatusResponse(**status_dict)


# ==========================================
# Detection Endpoints
# ==========================================

@router.post(
    "/detect",
    response_model=DetectionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error for invalid satellite format or bands"},
        503: {"model": ErrorResponse, "description": "Model is not loaded or weights are unavailable"}
    },
    tags=["Landslide Detection"],
    summary="Detect Landslides from Satellite Imagery (/detect)",
    description="""
Upload a multi-band satellite image to perform pixel-level landslide segmentation using the Hugging Face Prithvi model.

**Supported Satellite Input Formats:**
- **GeoTIFF (`.tif`, `.tiff`)**: Multi-band raster with 6 bands (`BLUE`, `GREEN`, `RED`, `NIR_BROAD`, `SWIR_1`, `SWIR_2`) or 14 bands (Landslide4Sense format). Geospatial CRS and affine transforms are automatically preserved.
- **HDF5 (`.h5`, `.hdf5`)**: Benchmark format containing multi-spectral array key `img` with 6 or 14 channels.

**Input Restrictions:**
- Standard 3-band photographic images (JPEG/PNG/ordinary camera photos) are **rejected**.
- Missing bands will not be synthesized or duplicated.
    """
)
async def detect_landslide(file: UploadFile = File(..., description="Satellite image file (GeoTIFF .tif or HDF5 .h5)")):
    try:
        response = await satellite_service.detect_landslides(file)
        return response
    except SatelliteValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Satellite Image Validation Failed",
                "message": str(e)
            }
        )
    except ModelLoadingError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "Prithvi Model Unavailable",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal Processing Error",
                "message": str(e)
            }
        )


# Backward compatibility alias for /api/satellite/detect
@router.post(
    "/satellite/detect",
    response_model=DetectionResponse,
    include_in_schema=False
)
async def detect_satellite_alias(file: UploadFile = File(...)):
    return await detect_landslide(file)


# ==========================================
# Result & Artifact Retrieval Endpoints
# ==========================================

@router.get(
    "/detect/{detection_id}",
    tags=["Landslide Detection"],
    summary="Retrieve Detection Result Metadata",
    description="Retrieve the analysis statistics, landslide pixel percentage, geospatial info, and file routes for a detection run."
)
async def get_detection_result(detection_id: str):
    metadata = satellite_service.get_result_metadata(detection_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with ID '{detection_id}' not found."
        )
    return metadata


@router.get(
    "/detect/{detection_id}/overlay",
    tags=["Landslide Detection"],
    summary="Retrieve Colored Overlay Image",
    description="Retrieve the visual colored overlay image highlighting detected landslide regions over the satellite base image."
)
async def get_overlay_image(detection_id: str):
    file_path = satellite_service.get_result_file_path(detection_id, "overlay")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Overlay image for detection '{detection_id}' not found."
        )
    return FileResponse(file_path, media_type="image/png", filename=f"overlay_{detection_id}.png")


@router.get(
    "/detect/{detection_id}/original",
    tags=["Landslide Detection"],
    summary="Retrieve Original Satellite RGB Image",
    description="Retrieve the RGB visual composite generated from the satellite input bands."
)
async def get_original_image(detection_id: str):
    file_path = satellite_service.get_result_file_path(detection_id, "original")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original visual image for detection '{detection_id}' not found."
        )
    return FileResponse(file_path, media_type="image/png", filename=f"original_{detection_id}.png")


@router.get(
    "/detect/{detection_id}/mask",
    tags=["Landslide Detection"],
    summary="Retrieve Binary Segmentation Mask Image",
    description="Retrieve the binary segmentation mask image (black: non-landslide, white: landslide)."
)
async def get_mask_image(detection_id: str):
    file_path = satellite_service.get_result_file_path(detection_id, "mask")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mask image for detection '{detection_id}' not found."
        )
    return FileResponse(file_path, media_type="image/png", filename=f"mask_{detection_id}.png")


@router.get(
    "/detect/{detection_id}/geotiff",
    tags=["Landslide Detection"],
    summary="Download Georeferenced Mask GeoTIFF",
    description="Download the georeferenced segmentation mask as a GeoTIFF raster preserving original CRS and affine transform."
)
async def get_geotiff_mask(detection_id: str):
    file_path = satellite_service.get_result_file_path(detection_id, "geotiff")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Georeferenced GeoTIFF for detection '{detection_id}' not found (input may not have had geospatial metadata)."
        )
    return FileResponse(
        file_path,
        media_type="image/tiff",
        filename=f"georeferenced_mask_{detection_id}.tif"
    )


# ==========================================
# Legacy / Compatibility Aliases
# ==========================================

@router.get("/satellite/results/{result_id}", include_in_schema=False)
async def legacy_get_result(result_id: str):
    return await get_detection_result(result_id)

@router.get("/satellite/results/{result_id}/overlay", include_in_schema=False)
async def legacy_get_overlay(result_id: str):
    return await get_overlay_image(result_id)

@router.get("/satellite/results/{result_id}/original", include_in_schema=False)
async def legacy_get_original(result_id: str):
    return await get_original_image(result_id)

@router.get("/satellite/results/{result_id}/mask", include_in_schema=False)
async def legacy_get_mask(result_id: str):
    return await get_mask_image(result_id)

@router.get("/satellite/results/{result_id}/geotiff", include_in_schema=False)
async def legacy_get_geotiff(result_id: str):
    return await get_geotiff_mask(result_id)
