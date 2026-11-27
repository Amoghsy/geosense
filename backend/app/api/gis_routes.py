import os
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.gis_schema import (
    GISHealthResponse,
    GISLayersListResponse,
    GISLayerMetadata,
    GISFeatureCollectionResponse,
    GISHotspotSummary,
    GISLocationResponse,
    GISSummaryResponse,
)
from app.services.gis_service import gis_service, STATES_GEOJSON_PATH
from app.db.database import DB_PATH

router = APIRouter(prefix="/gis", tags=["Phase 4 — GIS & Spatial Mapping"])


@router.get("/health", response_model=GISHealthResponse, summary="GIS Module Health")
async def gis_health():
    return GISHealthResponse(
        status="healthy",
        database_backend=f"SQLite ({os.path.basename(DB_PATH)}) + PostGIS schema ready",
        postgis_schema_available=True,
        ne_india_states_loaded=os.path.isfile(STATES_GEOJSON_PATH),
    )


@router.get("/layers", response_model=GISLayersListResponse, summary="List Available GIS Layers")
async def list_gis_layers():
    layers = gis_service.list_layers()
    return GISLayersListResponse(
        count=len(layers),
        layers=[GISLayerMetadata(**lyr) for lyr in layers],
    )


@router.get("/layers/{layer_id}", response_model=GISLayerMetadata, summary="Get GIS Layer Metadata")
async def get_gis_layer(layer_id: str):
    lyr = gis_service.get_layer(layer_id)
    if not lyr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GIS layer '{layer_id}' not found.",
        )
    return GISLayerMetadata(**lyr)


@router.get(
    "/layers/{layer_id}/features",
    response_model=GISFeatureCollectionResponse,
    summary="Query GeoJSON Features for a GIS Layer",
)
async def get_gis_layer_features(
    layer_id: str,
    bbox: Optional[str] = Query(None, description="min_lon,min_lat,max_lon,max_lat"),
    region: Optional[str] = Query(None, description="Filter by state/region name"),
    risk_category: Optional[str] = Query(None, description="Filter by LOW/MODERATE/HIGH/CRITICAL"),
    start_date: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    end_date: Optional[str] = Query(None, description="ISO timestamp upper bound"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        res = gis_service.get_layer_features(
            layer_id=layer_id,
            bbox=bbox,
            region=region,
            risk_category=risk_category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GIS layer '{layer_id}' not found.",
        )
    return GISFeatureCollectionResponse(**res)


@router.get("/regions/states", summary="Get NE India State Boundaries (GeoJSON)")
async def get_state_boundaries(state: Optional[str] = Query(None, description="Optional state name filter")):
    return gis_service.get_state_boundaries(state=state)


@router.get("/regions/districts", summary="Get District Boundaries (if available)")
async def get_district_boundaries(state: Optional[str] = Query(None)):
    return gis_service.get_district_boundaries(state=state)


@router.get("/hotspots", response_model=GISHotspotSummary, summary="Get GIS Hotspots (HIGH/CRITICAL)")
async def get_gis_hotspots(
    state: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    return GISHotspotSummary(**gis_service.get_hotspots(state=state, risk_category=risk_category, limit=limit))


@router.get("/location", response_model=GISLocationResponse, summary="Inspect GeoSense Data at Coordinates")
async def inspect_gis_location(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
):
    try:
        return GISLocationResponse(**gis_service.query_location(latitude, longitude))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/summary", response_model=GISSummaryResponse, summary="Get Real GIS Summary Statistics")
async def get_gis_summary():
    return GISSummaryResponse(**gis_service.get_summary())
