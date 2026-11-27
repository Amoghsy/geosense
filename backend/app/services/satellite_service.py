import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import UploadFile

from app.ml.preprocessing import preprocess_satellite_image, SatelliteValidationError
from app.ml.inference import run_landslide_inference
from app.ml.postprocessing import postprocess_landslide_detection
from app.ml.model_loader import get_model_manager
from app.schemas.satellite_schema import (
    DetectionResponse,
    DetectionStats,
    GeospatialMetadata,
    DetectionFiles
)

logger = logging.getLogger("geosense.satellite_service")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
RESULTS_DIR = os.getenv("RESULT_DIR", os.path.join(BASE_DIR, "results"))

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


class SatelliteService:
    def __init__(self):
        self.uploads_dir = os.path.abspath(UPLOADS_DIR)
        self.results_dir = os.path.abspath(RESULTS_DIR)

    async def detect_landslides(self, file: UploadFile) -> DetectionResponse:
        """
        Process uploaded satellite imagery:
        1. Save upload
        2. Preprocess multispectral bands & validate
        3. Execute Prithvi ViT inference (single patch or tiled)
        4. Postprocess masks, compute stats, and generate visual artifacts
        5. Persist metadata to structured folder and return API response
        """
        result_id = uuid.uuid4().hex[:12]
        detection_id = result_id

        original_ext = os.path.splitext(file.filename or "")[1].lower()
        if not original_ext:
            original_ext = ".tif"

        upload_filename = f"{result_id}_{file.filename}"
        upload_path = os.path.join(self.uploads_dir, upload_filename)

        # 1. Save uploaded file to disk
        try:
            contents = await file.read()
            if len(contents) == 0:
                raise SatelliteValidationError("Uploaded file is empty.")

            with open(upload_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            if isinstance(e, SatelliteValidationError):
                raise
            raise RuntimeError(f"Failed to save uploaded file: {str(e)}")

        # 2. Preprocess satellite imagery
        try:
            preprocessed = preprocess_satellite_image(upload_path)
        except Exception:
            raise

        # 3. Run actual Prithvi inference
        inference_out = run_landslide_inference(preprocessed)

        # 4. Postprocess segmentation masks and create artifacts
        post_out = postprocess_landslide_detection(
            preprocessed=preprocessed,
            inference=inference_out,
            result_id=result_id,
            results_dir=self.results_dir
        )

        # 5. Build file URLs / routes
        original_url = f"/detect/{result_id}/original"
        mask_url = f"/detect/{result_id}/mask"
        overlay_url = f"/detect/{result_id}/overlay"
        georef_url = f"/detect/{result_id}/geotiff" if post_out.georeferenced_mask_path else None
        result_json_url = f"/detect/{result_id}"

        detection_stats = DetectionStats(
            landslide_detected=post_out.landslide_detected,
            landslide_pixel_percentage=post_out.landslide_pixel_percentage,
            detected_area_percentage=post_out.detected_area_percentage,
            total_pixels=post_out.total_pixels,
            landslide_pixels=post_out.landslide_pixels,
            total_valid_pixels=post_out.total_valid_pixels,
            nodata_pixels=post_out.nodata_pixels
        )

        geospatial_meta = GeospatialMetadata(
            has_georeference=post_out.geospatial_metadata["has_georeference"],
            crs=post_out.geospatial_metadata["crs"],
            bounds=post_out.geospatial_metadata["bounds"],
            affine_transform=post_out.geospatial_metadata["affine_transform"],
            image_dimensions=post_out.image_dimensions
        )

        detection_files = DetectionFiles(
            original_image=original_url,
            segmentation_mask=mask_url,
            overlay=overlay_url,
            georeferenced_mask_tif=georef_url,
            result_json=result_json_url
        )

        manager = get_model_manager()
        total_time = round(inference_out.inference_time_seconds, 3)
        iso_timestamp = datetime.now(timezone.utc).isoformat()

        response = DetectionResponse(
            success=True,
            result_id=result_id,
            detection_id=detection_id,
            status="completed",
            model=manager.repo_id,
            model_version="main",
            timestamp=iso_timestamp,
            detection=detection_stats,
            geospatial=geospatial_meta,
            files=detection_files,
            processing_time_seconds=total_time
        )

        # 6. Save metadata JSON in structured detection directory and root results directory
        structured_meta_path = os.path.join(post_out.detection_dir, "result.json")
        legacy_meta_path = os.path.join(self.results_dir, f"meta_{result_id}.json")
        data_to_save = response.model_dump()
        with open(structured_meta_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
        with open(legacy_meta_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)

        return response

    def get_result_metadata(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis metadata by result_id / detection_id."""
        structured_meta = os.path.join(self.results_dir, "detections", result_id, "result.json")
        if os.path.isfile(structured_meta):
            with open(structured_meta, "r", encoding="utf-8") as f:
                return json.load(f)

        legacy_meta = os.path.join(self.results_dir, f"meta_{result_id}.json")
        if os.path.isfile(legacy_meta):
            with open(legacy_meta, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def get_result_file_path(self, result_id: str, file_type: str) -> Optional[str]:
        """
        Retrieve absolute path for a generated result file.
        file_type: 'original', 'mask', 'overlay', 'geotiff', 'json'
        """
        structured_dir = os.path.join(self.results_dir, "detections", result_id)
        structured_mapping = {
            "original": os.path.join(structured_dir, "original.png"),
            "mask": os.path.join(structured_dir, "mask.png"),
            "overlay": os.path.join(structured_dir, "overlay.png"),
            "geotiff": os.path.join(structured_dir, "georeferenced_mask.tif"),
            "json": os.path.join(structured_dir, "result.json"),
        }

        path = structured_mapping.get(file_type)
        if path and os.path.isfile(path):
            return path

        legacy_mapping = {
            "original": os.path.join(self.results_dir, f"original_{result_id}.png"),
            "mask": os.path.join(self.results_dir, f"mask_{result_id}.png"),
            "overlay": os.path.join(self.results_dir, f"overlay_{result_id}.png"),
            "geotiff": os.path.join(self.results_dir, f"georeferenced_mask_{result_id}.tif"),
            "json": os.path.join(self.results_dir, f"meta_{result_id}.json"),
        }
        legacy_path = legacy_mapping.get(file_type)
        if legacy_path and os.path.isfile(legacy_path):
            return legacy_path

        return None


satellite_service = SatelliteService()
