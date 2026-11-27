import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from PIL import Image
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.ml.susceptibility_model_loader import (
    get_susceptibility_model_manager,
    SUSCEPTIBILITY_REPO_ID,
    SUSCEPTIBILITY_REVISION,
)
from app.ml.susceptibility_preprocessing import (
    preprocess_susceptibility_input,
    SusceptibilityValidationError,
)
from app.db.database import get_susceptibility_analysis_record

client = TestClient(app)
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(autouse=True, scope="session")
def setup_phase2_fixtures():
    os.makedirs(TESTS_DIR, exist_ok=True)
    transform = from_bounds(91.85, 25.55, 91.90, 25.60, 224, 224)

    # 1. Valid 6-band multimodal GeoTIFF [B4, B3, B2, B8, DEM, Slope] in physical units
    tif_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.tif")
    if not os.path.exists(tif_path):
        rng = np.random.default_rng(42)
        rgb = rng.uniform(200.0, 2500.0, (3, 224, 224)).astype(np.float32)
        b8 = rng.uniform(500.0, 3500.0, (1, 224, 224)).astype(np.float32)
        dem = rng.uniform(500.0, 1800.0, (1, 224, 224)).astype(np.float32)
        slope = rng.uniform(5.0, 45.0, (1, 224, 224)).astype(np.float32)
        data = np.concatenate([rgb, b8, dem, slope], axis=0)
        with rasterio.open(
            tif_path, "w", driver="GTiff", height=224, width=224, count=6,
            dtype=np.float32, crs="EPSG:4326", transform=transform
        ) as dst:
            dst.write(data)
            dst.descriptions = ("B4_RED", "B3_GREEN", "B2_BLUE", "B8_NIR", "DEM", "SLOPE")

    # 2. Valid 6-band .npy array (normalized [0, 1])
    npy_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.npy")
    if not os.path.exists(npy_path):
        rng = np.random.default_rng(7)
        arr = rng.uniform(0.05, 0.95, (6, 224, 224)).astype(np.float32)
        np.save(npy_path, arr)

    # 3. Invalid 3-band RGB photo
    jpg_path = os.path.join(TESTS_DIR, "sample_photo.jpg")
    if not os.path.exists(jpg_path):
        Image.new("RGB", (64, 64), color=(100, 120, 140)).save(jpg_path)

    # 4. Invalid 3-band RGB GeoTIFF
    rgb_tif = os.path.join(TESTS_DIR, "sample_invalid_rgb.tif")
    if not os.path.exists(rgb_tif):
        t64 = from_bounds(91.85, 25.55, 91.90, 25.60, 64, 64)
        with rasterio.open(
            rgb_tif, "w", driver="GTiff", height=64, width=64, count=3,
            dtype=np.float32, crs="EPSG:4326", transform=t64
        ) as dst:
            dst.write(np.ones((3, 64, 64), dtype=np.float32) * 100)


def test_susceptibility_ui_and_health():
    ui_resp = client.get("/susceptibility-ui")
    assert ui_resp.status_code == 200
    assert "text/html" in ui_resp.headers["content-type"]

    health_resp = client.get("/susceptibility/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"


def test_susceptibility_model_status_and_info():
    status_resp = client.get("/susceptibility/model/status")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert s_data["model_repository"] == SUSCEPTIBILITY_REPO_ID
    assert s_data["model_revision"] == SUSCEPTIBILITY_REVISION
    assert len(s_data["required_channels"]) == 6

    info_resp = client.get("/susceptibility/model/info")
    assert info_resp.status_code == 200
    i_data = info_resp.json()
    assert i_data["license"] == "MIT"
    assert i_data["output_format"]["documented_decision_threshold"] == 0.291
    assert i_data["evaluation_metrics"]["roc_auc"] == 0.7371


def test_reject_rgb_photo_and_3band_geotiff():
    jpg_path = os.path.join(TESTS_DIR, "sample_photo.jpg")
    with open(jpg_path, "rb") as f:
        r1 = client.post("/susceptibility/analyze", files={"file": ("sample_photo.jpg", f, "image/jpeg")})
    assert r1.status_code == 400
    assert "cannot be fabricated" in r1.json()["detail"]["message"]

    rgb_tif = os.path.join(TESTS_DIR, "sample_invalid_rgb.tif")
    with open(rgb_tif, "rb") as f:
        r2 = client.post("/susceptibility/analyze", files={"file": ("sample_invalid_rgb.tif", f, "image/tiff")})
    assert r2.status_code == 400
    assert "3-band RGB GeoTIFF detected" in r2.json()["detail"]["message"]


def test_preprocessing_multimodal_geotiff_and_npy():
    tif_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.tif")
    prep = preprocess_susceptibility_input(tif_path)
    assert prep.rgb_tensor_chw.shape == (3, 224, 224)
    assert prep.terrain_tensor_chw.shape == (3, 224, 224)
    assert prep.has_georeference is True
    assert "4326" in str(prep.crs)
    assert 0.0 <= float(prep.terrain_tensor_chw.min()) <= float(prep.terrain_tensor_chw.max()) <= 1.0

    npy_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.npy")
    prep_npy = preprocess_susceptibility_input(npy_path)
    assert prep_npy.rgb_tensor_chw.shape == (3, 224, 224)
    assert prep_npy.has_georeference is False


def test_end_to_end_geotiff_inference_and_db_persistence():
    tif_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.tif")
    with open(tif_path, "rb") as f:
        resp = client.post(
            "/susceptibility/analyze",
            files={"file": ("sample_multimodal_6band.tif", f, "image/tiff")},
            data={"region_id": "meghalaya", "data_source": "Synthetic Test S2+SRTM"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["model_repository"] == SUSCEPTIBILITY_REPO_ID
    assert data["model_revision"] == SUSCEPTIBILITY_REVISION
    assert 0.0 <= data["prediction"]["susceptibility_score"] <= 1.0
    assert data["prediction"]["decision_threshold"] == 0.291
    assert data["prediction"]["susceptibility_class"] in {"Susceptible", "Non-Susceptible"}
    assert data["geographic"]["region_name"] == "Meghalaya"
    assert data["geographic"]["has_georeference"] is True
    assert data["geographic"]["coverage_status"] == "uncalibrated_prototype"

    aid = data["analysis_id"]

    # Verify SQLite persistence
    db_row = get_susceptibility_analysis_record(aid)
    assert db_row is not None
    assert db_row["id"] == aid
    assert db_row["region_id"] == "meghalaya"

    # Verify retrieval endpoints
    assert client.get(f"/susceptibility/analyze/{aid}").status_code == 200
    assert client.get(f"/susceptibility/analyze/{aid}/metadata").status_code == 200

    map_resp = client.get(f"/susceptibility/analyze/{aid}/map")
    assert map_resp.status_code == 200
    geojson = map_resp.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    rgb_prev = client.get(f"/susceptibility/analyze/{aid}/preview/rgb")
    assert rgb_prev.status_code == 200
    assert rgb_prev.headers["content-type"] == "image/png"

    terr_prev = client.get(f"/susceptibility/analyze/{aid}/preview/terrain")
    assert terr_prev.status_code == 200
    assert terr_prev.headers["content-type"] == "image/png"


def test_end_to_end_npy_inference_without_georef():
    npy_path = os.path.join(TESTS_DIR, "sample_multimodal_6band.npy")
    with open(npy_path, "rb") as f:
        resp = client.post(
            "/susceptibility/analyze",
            files={"file": ("sample_multimodal_6band.npy", f, "application/octet-stream")},
            data={"region_id": "sikkim", "latitude": "27.3389", "longitude": "88.6065"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["geographic"]["region_name"] == "Sikkim"
    assert data["geographic"]["has_georeference"] is False
    assert data["files"]["geojson_map"] is None
    assert client.get(f"/susceptibility/analyze/{data['analysis_id']}/map").status_code == 404
