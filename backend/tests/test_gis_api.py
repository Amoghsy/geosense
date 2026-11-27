import os
import sys
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.gis.geo_utils import (
    validate_coordinates,
    parse_bbox,
    transform_bounds_to_wgs84,
    mask_to_geojson_polygons,
    geometry_intersects_bbox,
)

client = TestClient(app)


def test_gis_ui_and_health():
    ui = client.get("/gis-ui")
    assert ui.status_code == 200
    assert "text/html" in ui.headers["content-type"]
    assert "Leaflet" in ui.text or "L.map" in ui.text

    h = client.get("/gis/health")
    assert h.status_code == 200
    data = h.json()
    assert data["status"] == "healthy"
    assert data["ne_india_states_loaded"] is True
    assert data["postgis_schema_available"] is True


def test_ne_india_states_and_districts_boundaries():
    resp = client.get("/gis/regions/states")
    assert resp.status_code == 200
    gj = resp.json()
    assert gj["type"] == "FeatureCollection"
    names = {f["properties"]["shapeName"] for f in gj["features"]}
    assert names == {
        "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Sikkim", "Tripura",
    }

    # Filter single state
    m_resp = client.get("/gis/regions/states", params={"state": "Meghalaya"})
    assert m_resp.status_code == 200
    assert len(m_resp.json()["features"]) == 1

    # Districts endpoint reports honest limitation rather than fabricating boundaries
    d_resp = client.get("/gis/regions/districts", params={"state": "Meghalaya"})
    assert d_resp.status_code == 200
    assert d_resp.json()["available"] is False


def test_geo_utils_crs_transform_bbox_and_mask_polygons(tmp_path):
    validate_coordinates(25.5788, 91.8933)
    with pytest.raises(ValueError):
        validate_coordinates(95.0, 91.8)

    bbox = parse_bbox("91.0,25.0,92.5,26.0")
    assert bbox == (91.0, 25.0, 92.5, 26.0)
    assert geometry_intersects_bbox({"type": "Point", "coordinates": [91.89, 25.57]}, bbox) is True
    assert geometry_intersects_bbox({"type": "Point", "coordinates": [88.60, 27.33]}, bbox) is False

    # UTM Zone 46N (EPSG:32646) -> WGS84 (EPSG:4326)
    utm_bounds = {"left": 380000.0, "bottom": 2820000.0, "right": 385000.0, "top": 2825000.0}
    wgs = transform_bounds_to_wgs84(utm_bounds, "EPSG:32646")
    assert 91.0 < wgs["left"] < 92.5
    assert 25.0 < wgs["bottom"] < 26.0

    # Synthetic georeferenced mask -> GeoJSON polygons
    tif_path = str(tmp_path / "synthetic_mask.tif")
    mask = np.zeros((32, 32), dtype=np.uint8)
    mask[8:16, 8:16] = 1
    tr = from_bounds(91.85, 25.55, 91.90, 25.60, 32, 32)
    with rasterio.open(
        tif_path, "w", driver="GTiff", height=32, width=32, count=1,
        dtype=np.uint8, crs="EPSG:4326", transform=tr
    ) as dst:
        dst.write(mask, 1)

    polys = mask_to_geojson_polygons(tif_path)
    assert len(polys) >= 1
    assert polys[0]["geometry"]["type"] == "Polygon"


def test_gis_layers_features_pagination_and_missing_layer():
    lyrs = client.get("/gis/layers")
    assert lyrs.status_code == 200
    data = lyrs.json()
    assert data["count"] == 8
    ids = {l["layer_id"] for l in data["layers"]}
    assert "phase1_detections" in ids
    assert "phase2_susceptibility" in ids
    assert "phase3_dynamic_risk" in ids
    assert "emergency_resources" in ids

    assert client.get("/gis/layers/phase3_dynamic_risk").status_code == 200
    assert client.get("/gis/layers/nonexistent_layer").status_code == 404

    fc_resp = client.get(
        "/gis/layers/phase3_dynamic_risk/features",
        params={"bbox": "88.0,21.0,97.5,30.0", "limit": 5, "offset": 0},
    )
    assert fc_resp.status_code == 200
    fc = fc_resp.json()
    assert fc["type"] == "FeatureCollection"
    assert fc["returned_count"] <= 5


def test_gis_location_hotspots_and_summary():
    # Shillong, Meghalaya point-in-polygon check
    loc = client.get("/gis/location", params={"latitude": 25.5788, "longitude": 91.8933})
    assert loc.status_code == 200
    assert loc.json()["state"] == "Meghalaya"

    hs = client.get("/gis/hotspots", params={"state": "Meghalaya"})
    assert hs.status_code == 200
    assert "methodology" in hs.json()

    sm = client.get("/gis/summary")
    assert sm.status_code == 200
    assert len(sm.json()["states_supported"]) == 8
