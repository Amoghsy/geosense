from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.resource_schema import (
    ResourceCreateRequest,
    ResourceUpdateRequest,
    ResourceVerifyRequest,
    ResourceAvailabilityUpdateRequest,
    ResourceResponse,
    ResourceListResponse,
    ResourceNearbyResponse,
    ResourceStatsResponse,
    ResourceRecommendationResponse,
)
from app.schemas.agent_schema import UserRole
from app.services.resource_service import resource_service

router = APIRouter(prefix="/resources", tags=["Phase 7 — Emergency Resource Management"])


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED, summary="Register Emergency Resource")
async def create_resource(
    req: ResourceCreateRequest,
    role: UserRole = Query("field_officer"),
    actor_id: Optional[str] = Query(None),
):
    try:
        return ResourceResponse(**resource_service.create_resource(req.model_dump(), actor_role=role, actor_id=actor_id))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=ResourceListResponse, summary="List & Filter Emergency Resources")
async def list_resources(
    role: UserRole = Query("citizen"),
    resource_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    operational_status: Optional[str] = Query(None),
    availability_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return ResourceListResponse(
        **resource_service.list_resources(
            role=role,
            resource_type=resource_type,
            state=state,
            district=district,
            verification_status=verification_status,
            operational_status=operational_status,
            availability_status=availability_status,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/near", response_model=ResourceNearbyResponse, summary="Search Nearby Verified Resources")
async def search_nearby_resources(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(25.0, ge=1.0, le=200.0),
    resource_type: Optional[str] = Query(None),
    operational_only: bool = Query(True),
    role: UserRole = Query("citizen"),
):
    try:
        return ResourceNearbyResponse(
            **resource_service.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                resource_type=resource_type,
                operational_only=operational_only,
                role=role,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/recommend", response_model=ResourceRecommendationResponse, summary="Advisory Resource Recommendations")
async def recommend_resources(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(25.0, ge=1.0, le=200.0),
    role: UserRole = Query("citizen"),
):
    return ResourceRecommendationResponse(
        **resource_service.recommend_resources(
            latitude=latitude, longitude=longitude, radius_km=radius_km, role=role
        )
    )


@router.get("/statistics", response_model=ResourceStatsResponse, summary="Emergency Resource Statistics")
async def resource_statistics(role: UserRole = Query("authority")):
    try:
        return ResourceStatsResponse(**resource_service.get_statistics(role=role))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/import-osm", summary="Import Candidate Facilities from OpenStreetMap (PENDING)")
async def import_osm_candidates(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(10.0, ge=1.0, le=25.0),
    role: UserRole = Query("authority"),
):
    try:
        return await resource_service.import_osm_candidates(
            latitude=latitude, longitude=longitude, radius_km=radius_km, actor_role=role
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Overpass API error: {exc}")


@router.get("/{resource_id}", response_model=ResourceResponse, summary="Get Emergency Resource Details")
async def get_resource(resource_id: str, role: UserRole = Query("citizen")):
    res = resource_service.get_resource(resource_id, role=role)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found or restricted.")
    return ResourceResponse(**res)


@router.patch("/{resource_id}", response_model=ResourceResponse, summary="Update Emergency Resource Details")
async def update_resource(
    resource_id: str,
    req: ResourceUpdateRequest,
    role: UserRole = Query("authority"),
    actor_id: Optional[str] = Query(None),
):
    try:
        res = resource_service.update_resource(resource_id, req.model_dump(exclude_none=True), actor_role=role, actor_id=actor_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")
    return ResourceResponse(**res)


@router.post("/{resource_id}/verify", response_model=ResourceResponse, summary="Verify or Reject Resource (Authority Only)")
async def verify_resource(
    resource_id: str,
    req: ResourceVerifyRequest,
    role: UserRole = Query("authority"),
    actor_id: Optional[str] = Query(None),
):
    try:
        res = resource_service.verify_resource(
            resource_id=resource_id,
            verification_status=req.verification_status,
            operational_status=req.operational_status,
            availability_status=req.availability_status,
            notes=req.notes,
            actor_role=role,
            actor_id=actor_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")
    return ResourceResponse(**res)


@router.patch("/{resource_id}/availability", response_model=ResourceResponse, summary="Update Operational & Availability Status")
async def update_availability(
    resource_id: str,
    req: ResourceAvailabilityUpdateRequest,
    role: UserRole = Query("authority"),
    actor_id: Optional[str] = Query(None),
):
    try:
        res = resource_service.update_availability(
            resource_id=resource_id,
            operational_status=req.operational_status,
            availability_status=req.availability_status,
            capacity=req.capacity,
            current_occupancy=req.current_occupancy,
            notes=req.notes,
            actor_role=role,
            actor_id=actor_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")
    return ResourceResponse(**res)


@router.get("/{resource_id}/history", summary="Retrieve Resource Verification & Status History")
async def get_resource_history(resource_id: str, role: UserRole = Query("authority")):
    try:
        hist = resource_service.get_history(resource_id, role=role)
        return {"resource_id": resource_id, "count": len(hist), "history": hist}
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
