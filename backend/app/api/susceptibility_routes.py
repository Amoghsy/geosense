from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.susceptibility_schema import (
    SusceptibilityHealthResponse,
    SusceptibilityModelStatusResponse,
    SusceptibilityModelInfoResponse,
    SusceptibilityAnalysisResponse,
)
from app.ml.susceptibility_model_loader import (
    get_susceptibility_model_manager,
    SusceptibilityModelError,
)
from app.ml.susceptibility_preprocessing import SusceptibilityValidationError
from app.services.susceptibility_service import susceptibility_service, NE_INDIA_REGIONS

router = APIRouter(prefix="/susceptibility", tags=["Phase 2 — Susceptibility Analysis"])


@router.get(
    "/health",
    response_model=SusceptibilityHealthResponse,
    summary="Phase 2 Module Health Check",
)
async def susceptibility_health():
    manager = get_susceptibility_model_manager()
    return SusceptibilityHealthResponse(
        status="healthy",
        model_loaded=manager.is_loaded(),
    )


@router.get(
    "/model/status",
    response_model=SusceptibilityModelStatusResponse,
    summary="Phase 2 Multimodal Model Status",
)
async def susceptibility_model_status():
    manager = get_susceptibility_model_manager()
    return SusceptibilityModelStatusResponse(**manager.get_status_info())


@router.get(
    "/model/info",
    response_model=SusceptibilityModelInfoResponse,
    summary="Phase 2 Verified Model Documentation & Metadata",
)
async def susceptibility_model_info():
    manager = get_susceptibility_model_manager()
    return SusceptibilityModelInfoResponse(**manager.get_model_info())


@router.get(
    "/regions",
    summary="Supported North Eastern India Regions",
)
async def list_supported_regions():
    return {"regions": NE_INDIA_REGIONS}


@router.post(
    "/analyze",
    response_model=SusceptibilityAnalysisResponse,
    summary="Run Multimodal Landslide Susceptibility Analysis",
    description=(
        "Accepts a 6-channel multimodal raster (.tif/.tiff) or NumPy (.npy) array "
        "with channels [B4 (Red), B3 (Green), B2 (Blue), B8 (NIR), DEM, Slope] and "
        "executes vinukatashidu/landslide-detection-multimodal."
    ),
)
async def analyze_susceptibility(
    file: UploadFile = File(..., description="6-channel GeoTIFF (.tif) or NumPy (.npy)"),
    region_id: Optional[str] = Form(None, description="NE India state key (e.g. meghalaya, sikkim, assam)"),
    latitude: Optional[float] = Form(None, description="Optional center latitude"),
    longitude: Optional[float] = Form(None, description="Optional center longitude"),
    data_source: Optional[str] = Form(None, description="Optional data source attribution"),
):
    try:
        return await susceptibility_service.analyze(
            file=file,
            region_id=region_id,
            latitude=latitude,
            longitude=longitude,
            data_source=data_source,
        )
    except SusceptibilityValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Multimodal Input Validation Failed",
                "message": str(exc),
            },
        )
    except SusceptibilityModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "Phase 2 Multimodal Model Unavailable",
                "message": str(exc),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Internal Susceptibility Processing Error",
                "message": str(exc),
            },
        )


@router.get(
    "/analyze/{analysis_id}",
    summary="Retrieve Previous Susceptibility Analysis",
)
async def get_analysis(analysis_id: str):
    result = susceptibility_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )
    return result


@router.get(
    "/analyze/{analysis_id}/map",
    summary="Retrieve Generated GeoJSON Susceptibility Map",
)
async def get_analysis_map(analysis_id: str):
    path = susceptibility_service.get_artifact_path(analysis_id, "map")
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Geographic GeoJSON map for analysis '{analysis_id}' is not available "
                "(input lacked geospatial CRS/transform or analysis ID does not exist)."
            ),
        )
    return FileResponse(path, media_type="application/geo+json", filename=f"susceptibility_{analysis_id}.geojson")


@router.get(
    "/analyze/{analysis_id}/metadata",
    summary="Retrieve Analysis Metadata",
)
async def get_analysis_metadata(analysis_id: str):
    path = susceptibility_service.get_artifact_path(analysis_id, "metadata")
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata for analysis '{analysis_id}' not found.",
        )
    return FileResponse(path, media_type="application/json", filename=f"metadata_{analysis_id}.json")


@router.get(
    "/analyze/{analysis_id}/preview/{preview_type}",
    summary="Retrieve RGB or Terrain Preview Image",
)
async def get_analysis_preview(analysis_id: str, preview_type: str):
    if preview_type not in {"rgb", "terrain"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="preview_type must be 'rgb' or 'terrain'.")
    path = susceptibility_service.get_artifact_path(analysis_id, preview_type)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preview '{preview_type}' for analysis '{analysis_id}' not found.",
        )
    return FileResponse(path, media_type="image/png", filename=f"{preview_type}_{analysis_id}.png")
