import os
import json
import glob
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from shapely.geometry import Point, shape, box, mapping

from app.db.database import get_db_connection, init_db, DB_PATH
from app.gis.geo_utils import (
    validate_coordinates,
    parse_bbox,
    transform_bounds_to_wgs84,
    mask_to_geojson_polygons,
    geometry_intersects_bbox,
)

logger = logging.getLogger("geosense.gis_service")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.abspath(os.getenv("RESULT_DIR", os.path.join(BASE_DIR, "results")))
STATES_GEOJSON_PATH = os.path.join(BASE_DIR, "app", "data", "ne_india_states.geojson")

NE_STATES_LIST = [
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
]


class GISService:
    def __init__(self):
        self._states_cache: Optional[Dict[str, Any]] = None
        self._layer_enabled_state: Dict[str, bool] = {}
        init_db()

    def _load_states_geojson(self) -> Dict[str, Any]:
        if self._states_cache is not None:
            return self._states_cache
        if not os.path.isfile(STATES_GEOJSON_PATH):
            return {
                "type": "FeatureCollection",
                "source": "Unavailable",
                "features": [],
            }
        with open(STATES_GEOJSON_PATH, "r", encoding="utf-8") as f:
            self._states_cache = json.load(f)
        return self._states_cache

    def _find_state_for_point(self, lat: float, lon: float) -> Optional[str]:
        gj = self._load_states_geojson()
        pt = Point(lon, lat)
        for feat in gj.get("features", []):
            geom = shape(feat["geometry"])
            if geom.contains(pt):
                return feat.get("properties", {}).get("shapeName")
        return None

    def _get_phase1_features(self) -> List[Dict[str, Any]]:
        """Read verified Phase 1 Prithvi detections with valid geospatial bounds/masks."""
        features: List[Dict[str, Any]] = []
        det_dir = os.path.join(RESULTS_DIR, "detections")
        if not os.path.isdir(det_dir):
            return features

        for meta_path in glob.glob(os.path.join(det_dir, "*", "result.json")):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                geo = meta.get("geospatial", {})
                if not geo.get("has_georeference") or not geo.get("bounds"):
                    continue
                crs_str = geo.get("crs") or "EPSG:4326"
                wgs_bounds = transform_bounds_to_wgs84(geo["bounds"], crs_str)
                footprint = mapping(
                    box(
                        wgs_bounds["left"],
                        wgs_bounds["bottom"],
                        wgs_bounds["right"],
                        wgs_bounds["top"],
                    )
                )
                det = meta.get("detection", {})
                ts = meta.get("timestamp")
                did = meta.get("detection_id") or meta.get("result_id")
                cx = (wgs_bounds["left"] + wgs_bounds["right"]) / 2.0
                cy = (wgs_bounds["bottom"] + wgs_bounds["top"]) / 2.0
                state = self._find_state_for_point(cy, cx)

                # Extract polygonized landslide mask features if landslides detected
                georef_tif = os.path.join(os.path.dirname(meta_path), "georeferenced_mask.tif")
                poly_feats = mask_to_geojson_polygons(georef_tif, max_polygons=50) if det.get("landslide_detected") else []

                features.append(
                    {
                        "type": "Feature",
                        "id": f"p1_{did}",
                        "geometry": footprint,
                        "properties": {
                            "layer": "phase1_detections",
                            "detection_id": did,
                            "model": meta.get("model"),
                            "landslide_detected": det.get("landslide_detected"),
                            "landslide_pixel_percentage": det.get("landslide_pixel_percentage"),
                            "timestamp": ts,
                            "source_crs": crs_str,
                            "region": state,
                            "mask_polygons_count": len(poly_feats),
                        },
                    }
                )
                for idx, pf in enumerate(poly_feats):
                    pf["id"] = f"p1_{did}_poly_{idx}"
                    pf["properties"].update(
                        {
                            "layer": "phase1_detections",
                            "detection_id": did,
                            "timestamp": ts,
                            "region": state,
                            "feature_kind": "landslide_mask_polygon",
                        }
                    )
                    features.append(pf)
            except Exception as exc:
                logger.warning(f"Skipping Phase 1 feature {meta_path}: {exc}")
        return features

    def _get_phase2_features(self) -> List[Dict[str, Any]]:
        """Read verified Phase 2 susceptibility analyses with valid coordinates or GeoJSON."""
        features: List[Dict[str, Any]] = []
        if not os.path.isfile(DB_PATH):
            return features
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM susceptibility_analyses ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
            for r in rows:
                aid = r["id"]
                geojson_path = os.path.join(RESULTS_DIR, "susceptibility", aid, "susceptibility_map.geojson")
                if os.path.isfile(geojson_path):
                    with open(geojson_path, "r", encoding="utf-8") as f:
                        gj = json.load(f)
                    for idx, feat in enumerate(gj.get("features", [])):
                        feat["id"] = f"p2_{aid}_{idx}"
                        feat["properties"]["analysis_id"] = aid
                        feat["properties"]["region"] = r["region_id"]
                        feat["properties"]["coverage_status"] = r["coverage_status"]
                        feat["properties"]["timestamp"] = r["created_at"]
                        features.append(feat)
                elif r["latitude"] is not None and r["longitude"] is not None:
                    features.append(
                        {
                            "type": "Feature",
                            "id": f"p2_{aid}",
                            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
                            "properties": {
                                "analysis_id": aid,
                                "susceptibility_score": r["susceptibility_value"],
                                "susceptibility_class": r["susceptibility_class"],
                                "region": r["region_id"],
                                "coverage_status": r["coverage_status"],
                                "model_repository": r["model_repository"],
                                "timestamp": r["created_at"],
                            },
                        }
                    )
        finally:
            conn.close()
        return features

    def _get_phase3_risk_features(self, layer_kind: str = "risk") -> List[Dict[str, Any]]:
        """Read latest Phase 3 dynamic risk / rainfall / terrain features per location."""
        features: List[Dict[str, Any]] = []
        if not os.path.isfile(DB_PATH):
            return features
        conn = get_db_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM risk_assessments r1
                WHERE assessment_time = (
                    SELECT MAX(r2.assessment_time) FROM risk_assessments r2
                    WHERE r2.location_id = r1.location_id
                )
                ORDER BY assessment_time DESC LIMIT 500
                """
            ).fetchall()
            for r in rows:
                payload = json.loads(r["raw_payload"])
                state = self._find_state_for_point(r["latitude"], r["longitude"])
                if layer_kind == "risk":
                    props = {
                        "assessment_id": r["id"],
                        "location_id": r["location_id"],
                        "location_name": payload.get("location_name"),
                        "risk_score": r["risk_score"],
                        "risk_category": r["risk_category"],
                        "completeness_score": r["completeness_score"],
                        "missing_factors": json.loads(r["missing_factors"]),
                        "explanation": r["explanation"],
                        "region": state,
                        "timestamp": r["assessment_time"],
                    }
                elif layer_kind == "rainfall":
                    rain = payload.get("rainfall_indicators", {})
                    obs = rain.get("observed_windows", {})
                    fc = rain.get("forecast_windows", {})
                    props = {
                        "location_id": r["location_id"],
                        "location_name": payload.get("location_name"),
                        "rainfall_24h_mm": obs.get("24h", {}).get("rainfall_mm"),
                        "rainfall_72h_mm": obs.get("72h", {}).get("rainfall_mm"),
                        "forecast_24h_mm": fc.get("next_24h", {}).get("rainfall_mm"),
                        "awi_proxy": rain.get("awi_proxy", {}).get("awi_value"),
                        "region": state,
                        "timestamp": r["assessment_time"],
                    }
                else:
                    terr = payload.get("terrain_info", {})
                    if not terr.get("available"):
                        continue
                    props = {
                        "location_id": r["location_id"],
                        "elevation_m": terr.get("elevation_m"),
                        "slope_deg": terr.get("slope_deg"),
                        "terrain_score": terr.get("terrain_score"),
                        "region": state,
                        "timestamp": r["assessment_time"],
                    }
                features.append(
                    {
                        "type": "Feature",
                        "id": f"p3_{layer_kind}_{r['id']}",
                        "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
                        "properties": props,
                    }
                )
        finally:
            conn.close()
        return features

    def _get_table_point_features(self, table: str, where_clause: str = "") -> List[Dict[str, Any]]:
        features: List[Dict[str, Any]] = []
        if not os.path.isfile(DB_PATH):
            return features
        conn = get_db_connection()
        try:
            sql = f"SELECT * FROM {table} {where_clause} ORDER BY created_at DESC LIMIT 500"
            for r in conn.execute(sql).fetchall():
                d = dict(r)
                lat = d.pop("latitude")
                lon = d.pop("longitude")
                features.append(
                    {
                        "type": "Feature",
                        "id": d["id"],
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": d,
                    }
                )
        finally:
            conn.close()
        return features

    def list_layers(self) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        p1 = self._get_phase1_features()
        p2 = self._get_phase2_features()
        p3_risk = self._get_phase3_risk_features("risk")
        p3_rain = self._get_phase3_risk_features("rainfall")
        terrain = self._get_phase3_risk_features("terrain")
        cit_inc = self._get_table_point_features("incidents", "WHERE reporter_type = 'citizen'")
        ver_inc = self._get_table_point_features("incidents", "WHERE status = 'verified'")
        res_pts = self._get_table_point_features("emergency_resources")

        catalog = [
            {
                "layer_id": "phase1_detections",
                "layer_name": "Satellite Landslide Detections (Phase 1)",
                "layer_type": "polygon",
                "source": "IBM/NASA Prithvi-EO-2.0-300M (srivassid/prithvi-landslide)",
                "description": "Georeferenced satellite footprints and detected landslide mask polygons.",
                "crs": "EPSG:4326",
                "geographic_coverage": "Uploaded Sentinel-2 / Landslide4Sense scenes",
                "resolution": "10m (Sentinel-2)",
                "last_updated": now_iso,
                "availability_status": "available" if p1 else "empty",
                "feature_count": len(p1),
            },
            {
                "layer_id": "phase2_susceptibility",
                "layer_name": "Multimodal Baseline Susceptibility (Phase 2)",
                "layer_type": "polygon_or_point",
                "source": "vinukatashidu/landslide-detection-multimodal",
                "description": "Patch-level susceptibility scores (uncalibrated academic prototype).",
                "crs": "EPSG:4326",
                "geographic_coverage": "Uploaded 6-channel multimodal patches",
                "resolution": "224x224 patch",
                "last_updated": now_iso,
                "availability_status": "available" if p2 else "empty",
                "feature_count": len(p2),
            },
            {
                "layer_id": "phase3_dynamic_risk",
                "layer_name": "Dynamic Weather-Integrated Risk (Phase 3)",
                "layer_type": "point",
                "source": "GeoSense Dynamic Risk Fusion Engine + Open-Meteo",
                "description": "Latest 0-100 heuristic risk index and category per assessed location.",
                "crs": "EPSG:4326",
                "geographic_coverage": "North Eastern India assessed coordinates",
                "resolution": "Open-Meteo grid (~11-25 km)",
                "last_updated": now_iso,
                "availability_status": "available" if p3_risk else "empty",
                "feature_count": len(p3_risk),
            },
            {
                "layer_id": "phase3_rainfall",
                "layer_name": "Observed & Forecast Rainfall (Phase 3)",
                "layer_type": "point",
                "source": "Open-Meteo Forecast & Historical Archive APIs",
                "description": "24h/72h observed rainfall, 24h forecast, and AWI proxy.",
                "crs": "EPSG:4326",
                "geographic_coverage": "North Eastern India assessed coordinates",
                "resolution": "Open-Meteo grid",
                "last_updated": now_iso,
                "availability_status": "available" if p3_rain else "empty",
                "feature_count": len(p3_rain),
            },
            {
                "layer_id": "terrain_attributes",
                "layer_name": "Verified Terrain Attributes",
                "layer_type": "point",
                "source": "User/GIS supplied elevation and slope",
                "description": "Verified elevation (m) and slope (deg) attached to assessments.",
                "crs": "EPSG:4326",
                "geographic_coverage": "Assessed points with terrain inputs",
                "resolution": "Point",
                "last_updated": now_iso,
                "availability_status": "available" if terrain else "empty",
                "feature_count": len(terrain),
            },
            {
                "layer_id": "citizen_incidents",
                "layer_name": "Citizen-Reported Incidents",
                "layer_type": "point",
                "source": "GeoSense Citizen Reporting",
                "description": "Unverified citizen-submitted landslide reports.",
                "crs": "EPSG:4326",
                "geographic_coverage": "North Eastern India",
                "resolution": "Point",
                "last_updated": now_iso,
                "availability_status": "available" if cit_inc else "unavailable",
                "feature_count": len(cit_inc),
            },
            {
                "layer_id": "verified_incidents",
                "layer_name": "Field-Officer Verified Incidents",
                "layer_type": "point",
                "source": "GeoSense Field Officer Verification",
                "description": "Verified landslide incidents confirmed by field officers.",
                "crs": "EPSG:4326",
                "geographic_coverage": "North Eastern India",
                "resolution": "Point",
                "last_updated": now_iso,
                "availability_status": "available" if ver_inc else "unavailable",
                "feature_count": len(ver_inc),
            },
            {
                "layer_id": "emergency_resources",
                "layer_name": "Emergency Resources (Hospitals & Shelters)",
                "layer_type": "point",
                "source": "Pending verified GIS emergency dataset",
                "description": "Hospitals, shelters, and rescue centres (not populated with invented data).",
                "crs": "EPSG:4326",
                "geographic_coverage": "North Eastern India",
                "resolution": "Point",
                "last_updated": now_iso,
                "availability_status": "available" if res_pts else "unavailable",
                "feature_count": len(res_pts),
            },
        ]

        for item in catalog:
            item["enabled"] = self._layer_enabled_state.get(item["layer_id"], True)
        return catalog

    def get_layer(self, layer_id: str) -> Optional[Dict[str, Any]]:
        for lyr in self.list_layers():
            if lyr["layer_id"] == layer_id:
                return lyr
        return None

    def get_layer_features(
        self,
        layer_id: str,
        bbox: Optional[str] = None,
        region: Optional[str] = None,
        risk_category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        raw_map = {
            "phase1_detections": lambda: self._get_phase1_features(),
            "phase2_susceptibility": lambda: self._get_phase2_features(),
            "phase3_dynamic_risk": lambda: self._get_phase3_risk_features("risk"),
            "phase3_rainfall": lambda: self._get_phase3_risk_features("rainfall"),
            "terrain_attributes": lambda: self._get_phase3_risk_features("terrain"),
            "citizen_incidents": lambda: self._get_table_point_features("incidents", "WHERE reporter_type = 'citizen'"),
            "verified_incidents": lambda: self._get_table_point_features("incidents", "WHERE status = 'verified'"),
            "emergency_resources": lambda: self._get_table_point_features("emergency_resources"),
        }
        if layer_id not in raw_map:
            return None

        feats = raw_map[layer_id]()
        bbox_tuple = parse_bbox(bbox) if bbox else None

        filtered: List[Dict[str, Any]] = []
        for f in feats:
            props = f.get("properties", {})
            if bbox_tuple and not geometry_intersects_bbox(f["geometry"], bbox_tuple):
                continue
            if region:
                reg_val = str(props.get("region") or "").lower()
                if region.lower() not in reg_val:
                    continue
            if risk_category:
                if str(props.get("risk_category") or "").upper() != risk_category.upper():
                    continue
            ts = props.get("timestamp") or props.get("created_at")
            if start_date and ts and str(ts) < start_date:
                continue
            if end_date and ts and str(ts) > end_date:
                continue
            filtered.append(f)

        paginated = filtered[offset : offset + limit]
        return {
            "type": "FeatureCollection",
            "layer_id": layer_id,
            "crs": "EPSG:4326",
            "total_matched": len(filtered),
            "returned_count": len(paginated),
            "features": paginated,
        }

    def get_state_boundaries(self, state: Optional[str] = None) -> Dict[str, Any]:
        gj = self._load_states_geojson()
        if not state:
            return gj
        feats = [
            f for f in gj.get("features", [])
            if str(f.get("properties", {}).get("shapeName", "")).lower() == state.strip().lower()
        ]
        return {
            "type": "FeatureCollection",
            "source": gj.get("source"),
            "license": gj.get("license"),
            "crs": "EPSG:4326",
            "features": feats,
        }

    def get_district_boundaries(self, state: Optional[str] = None) -> Dict[str, Any]:
        return {
            "available": False,
            "state": state,
            "message": (
                "District-level (ADM2) boundary polygons are not bundled in this deployment; "
                "verified state-level (ADM1) boundaries from geoBoundaries IND ADM1 (CC BY 2.5 IN) are available at /gis/regions/states."
            ),
            "features": [],
        }

    def get_hotspots(
        self,
        state: Optional[str] = None,
        risk_category: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        feats = self._get_phase3_risk_features("risk")
        hotspots = []
        for f in feats:
            p = f["properties"]
            cat = p.get("risk_category")
            if cat not in {"HIGH", "CRITICAL"}:
                continue
            if risk_category and cat != risk_category.upper():
                continue
            if state and str(p.get("region") or "").lower() != state.strip().lower():
                continue
            hotspots.append(
                {
                    "location_id": p["location_id"],
                    "location_name": p.get("location_name"),
                    "state": p.get("region"),
                    "coordinates": f["geometry"]["coordinates"],
                    "risk_score": p.get("risk_score"),
                    "risk_category": cat,
                    "assessment_time": p.get("timestamp"),
                }
            )
        return {
            "count": len(hotspots[:limit]),
            "methodology": (
                "Aggregates latest Phase 3 assessments per 0.001-deg grid cell where risk_category is HIGH or CRITICAL. "
                "Represents a collection of elevated heuristic risk points, not a statistically validated spatial cluster model."
            ),
            "hotspots": hotspots[:limit],
        }

    def query_location(self, latitude: float, longitude: float) -> Dict[str, Any]:
        validate_coordinates(latitude, longitude)
        state = self._find_state_for_point(latitude, longitude)

        # Find nearest Phase 3 risk assessment within ~0.2 deg (~22 km)
        nearest_risk = None
        min_dist = 0.2
        for f in self._get_phase3_risk_features("risk"):
            lon2, lat2 = f["geometry"]["coordinates"]
            dist = ((latitude - lat2) ** 2 + (longitude - lon2) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_risk = f["properties"]

        # Find intersecting Phase 1 detections
        pt = Point(longitude, latitude)
        intersecting_p1 = [
            f["properties"]
            for f in self._get_phase1_features()
            if shape(f["geometry"]).contains(pt)
        ]

        # Find nearest Phase 2 susceptibility within ~0.2 deg
        nearest_p2 = None
        min_p2 = 0.2
        for f in self._get_phase2_features():
            geom = shape(f["geometry"])
            if geom.contains(pt):
                nearest_p2 = f["properties"]
                break
            d = geom.distance(pt)
            if d < min_p2:
                min_p2 = d
                nearest_p2 = f["properties"]

        return {
            "latitude": latitude,
            "longitude": longitude,
            "state": state,
            "district_note": "District boundaries unavailable; state resolved via geoBoundaries IND ADM1.",
            "dynamic_risk": nearest_risk,
            "susceptibility": nearest_p2,
            "satellite_detections": intersecting_p1,
            "incidents": [],
        }

    def get_summary(self) -> Dict[str, Any]:
        p3 = self._get_phase3_risk_features("risk")
        high_cnt = sum(1 for f in p3 if f["properties"].get("risk_category") == "HIGH")
        crit_cnt = sum(1 for f in p3 if f["properties"].get("risk_category") == "CRITICAL")
        p1 = self._get_phase1_features()
        p2 = self._get_phase2_features()
        inc = self._get_table_point_features("incidents")
        res = self._get_table_point_features("emergency_resources")

        return {
            "total_risk_assessments": len(p3),
            "high_risk_locations": high_cnt,
            "critical_risk_locations": crit_cnt,
            "available_detection_features": len(p1),
            "available_susceptibility_analyses": len(p2),
            "reported_incidents": len(inc),
            "emergency_resources": len(res),
            "states_supported": NE_STATES_LIST,
        }


gis_service = GISService()
