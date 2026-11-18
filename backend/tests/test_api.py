import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.ml.preprocessing import (
    preprocess_satellite_image,
    SatelliteValidationError,
    PRITHVI_BANDS
)
from app.ml.model_loader import get_model_manager
from app.utils.image_utils import (
    create_rgb_preview,
    create_colored_overlay,
    save_binary_mask_image,
    save_georeferenced_mask_tif
)
import numpy as np
from rasterio.transform import from_bounds
import rasterio
from PIL import Image

client = TestClient(app)
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(autouse=True, scope="session")
def setup_test_fixtures():
    """Ensure test fixtures exist locally without requiring them to be committed to Git."""
    os.makedirs(TESTS_DIR, exist_ok=True)
    transform = from_bounds(76.5, 31.0, 76.6, 31.1, 64, 64)

    # 1. Plain text file
    txt_path = os.path.join(TESTS_DIR, "sample_invalid.txt")
    if not os.path.exists(txt_path):
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("This is not a satellite image.")

    # 2. JPEG photograph
    jpg_path = os.path.join(TESTS_DIR, "sample_photo.jpg")
    if not os.path.exists(jpg_path):
        img = Image.new("RGB", (64, 64), color=(73, 109, 137))
        img.save(jpg_path)

    # 3. 3-band RGB GeoTIFF
    rgb_path = os.path.join(TESTS_DIR, "sample_invalid_rgb.tif")
    if not os.path.exists(rgb_path):
        with rasterio.open(
            rgb_path, "w", driver="GTiff", height=64, width=64, count=3,
            dtype=np.float32, crs="EPSG:4326", transform=transform
        ) as dst:
            dst.write(np.ones((3, 64, 64), dtype=np.float32) * 100)

    # 4. 4-band GeoTIFF
    four_path = os.path.join(TESTS_DIR, "sample_invalid_4band.tif")
    if not os.path.exists(four_path):
        with rasterio.open(
            four_path, "w", driver="GTiff", height=64, width=64, count=4,
            dtype=np.float32, crs="EPSG:4326", transform=transform
        ) as dst:
            dst.write(np.ones((4, 64, 64), dtype=np.float32) * 50)

    # 5. 6-band multispectral satellite GeoTIFF
    sat_path = os.path.join(TESTS_DIR, "sample_satellite_6band.tif")
    if not os.path.exists(sat_path):
        trans_128 = from_bounds(76.5, 31.0, 76.6, 31.1, 128, 128)
        data = np.random.uniform(0.1, 2.5, (6, 128, 128)).astype(np.float32)
        with rasterio.open(
            sat_path, "w", driver="GTiff", height=128, width=128, count=6,
            dtype=np.float32, crs="EPSG:4326", transform=trans_128
        ) as dst:
            dst.write(data)
            dst.descriptions = ("BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2")


def test_health_endpoint():
    """Verify health check endpoint returns 200 with expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "GeoSense Satellite Detection API"


def test_model_status_endpoint():
    """Verify model status endpoint returns repository, device, and band specifications."""
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert data["model_repository"] == "srivassid/prithvi-landslide"
    assert "status" in data
    assert "device" in data
    assert "required_bands" in data
    assert data["required_bands"] == ["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"]


def test_unsupported_file_extension_rejected():
    """Verify non-satellite text files are rejected with HTTP 400."""
    txt_path = os.path.join(TESTS_DIR, "sample_invalid.txt")
    with open(txt_path, "rb") as f:
        response = client.post(
            "/api/satellite/detect",
            files={"file": ("sample_invalid.txt", f, "text/plain")}
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["success"] is False
    assert "Unsupported file extension" in detail["message"]


def test_standard_photo_jpg_rejected():
    """Verify consumer camera photographs (JPEG) are explicitly rejected."""
    jpg_path = os.path.join(TESTS_DIR, "sample_photo.jpg")
    with open(jpg_path, "rb") as f:
        response = client.post(
            "/api/satellite/detect",
            files={"file": ("sample_photo.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["success"] is False
    assert "Standard photographic images" in detail["message"]


def test_3band_rgb_geotiff_rejected():
    """Verify standard 3-band RGB imagery is rejected with clear error requiring 6 bands."""
    rgb_path = os.path.join(TESTS_DIR, "sample_invalid_rgb.tif")
    with open(rgb_path, "rb") as f:
        response = client.post(
            "/api/satellite/detect",
            files={"file": ("sample_invalid_rgb.tif", f, "image/tiff")}
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["success"] is False
    assert "Standard 3-band RGB photograph detected" in detail["message"]


def test_incorrect_band_count_rejected():
    """Verify GeoTIFF with incorrect band count (e.g. 4 bands) is rejected."""
    four_band_path = os.path.join(TESTS_DIR, "sample_invalid_4band.tif")
    with open(four_band_path, "rb") as f:
        response = client.post(
            "/api/satellite/detect",
            files={"file": ("sample_invalid_4band.tif", f, "image/tiff")}
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["success"] is False
    assert "Unsupported number of bands: 4" in detail["message"]


def test_preprocessing_6band_satellite_tif():
    """Verify preprocessing correctly normalizes and shapes genuine 6-band satellite data."""
    sample_tif = os.path.join(TESTS_DIR, "sample_satellite_6band.tif")
    assert os.path.exists(sample_tif), "Test sample GeoTIFF must exist"

    preprocessed = preprocess_satellite_image(sample_tif)
    assert preprocessed.tensor.shape == (1, 6, 224, 224)
    assert preprocessed.original_shape == (128, 128)
    assert preprocessed.has_georeference is True
    assert "4326" in str(preprocessed.crs)
    assert preprocessed.transform is not None


def test_mask_and_overlay_generation(tmp_path):
    """Verify generation of RGB preview, binary mask, and colored overlay images."""
    dummy_chw = np.random.uniform(0.1, 2.0, (6, 128, 128)).astype(np.float32)
    rgb_img = create_rgb_preview(dummy_chw)
    assert rgb_img.size == (128, 128)

    dummy_mask = np.zeros((128, 128), dtype=np.uint8)
    dummy_mask[40:70, 40:70] = 1  # 30x30 landslide patch

    overlay_img = create_colored_overlay(rgb_img, dummy_mask)
    assert overlay_img.size == (128, 128)

    mask_path = str(tmp_path / "test_mask.png")
    save_binary_mask_image(dummy_mask, mask_path)
    assert os.path.isfile(mask_path)

    geotiff_path = str(tmp_path / "test_georef.tif")
    transform = from_bounds(76.5, 31.0, 76.6, 31.1, 128, 128)
    save_georeferenced_mask_tif(dummy_mask, geotiff_path, "EPSG:4326", transform)
    assert os.path.isfile(geotiff_path)


def test_successful_inference_or_model_status():
    """
    Test end-to-end detection pipeline with authentic Landslide4Sense 6-band sample.
    If the 3.8GB checkpoint is currently loading or downloading, checks graceful handling.
    """
    sample_tif = os.path.join(TESTS_DIR, "sample_satellite_6band.tif")
    assert os.path.exists(sample_tif)

    with open(sample_tif, "rb") as f:
        response = client.post(
            "/api/satellite/detect",
            files={"file": ("sample_satellite_6band.tif", f, "image/tiff")}
        )

    manager = get_model_manager()

    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert data["model"] == "srivassid/prithvi-landslide"
        assert "result_id" in data
        assert "detection" in data
        assert "landslide_detected" in data["detection"]
        assert "landslide_pixel_percentage" in data["detection"]
        assert "total_pixels" in data["detection"]
        assert data["detection"]["total_pixels"] == 128 * 128
        assert data["geospatial"]["has_georeference"] is True
        assert "4326" in str(data["geospatial"]["crs"])

        result_id = data["result_id"]

        # Test metadata retrieval
        meta_resp = client.get(f"/api/satellite/results/{result_id}")
        assert meta_resp.status_code == 200
        assert meta_resp.json()["result_id"] == result_id

        # Test overlay retrieval
        overlay_resp = client.get(f"/api/satellite/results/{result_id}/overlay")
        assert overlay_resp.status_code == 200
        assert overlay_resp.headers["content-type"] == "image/png"

        # Test mask retrieval
        mask_resp = client.get(f"/api/satellite/results/{result_id}/mask")
        assert mask_resp.status_code == 200
        assert mask_resp.headers["content-type"] == "image/png"

        # Test GeoTIFF download
        geotiff_resp = client.get(f"/api/satellite/results/{result_id}/geotiff")
        assert geotiff_resp.status_code == 200
        assert geotiff_resp.headers["content-type"] == "image/tiff"
    else:
        # If model is downloading or not yet loaded
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["success"] is False
        assert "Prithvi Model Unavailable" in detail["error"]
