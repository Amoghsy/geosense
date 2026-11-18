import os
import uuid
import json
import logging
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
        2. Preprocess multispectral bands
        3. Execute Prithvi ViT inference
        4. Postprocess masks and generate visualization
        5. Persist metadata and return structured API response
        """
        result_id = uuid.uuid4().hex[:12]
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
            # Clean up upload file on preprocessing failure if needed
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
        original_url = f"/api/satellite/results/{result_id}/original"
        mask_url = f"/api/satellite/results/{result_id}/mask"
        overlay_url = f"/api/satellite/results/{result_id}/overlay"
        georef_url = f"/api/satellite/results/{result_id}/geotiff" if post_out.georeferenced_mask_path else None

        detection_stats = DetectionStats(
            landslide_detected=post_out.landslide_detected,
            landslide_pixel_percentage=post_out.landslide_pixel_percentage,
            total_pixels=post_out.total_pixels,
            landslide_pixels=post_out.landslide_pixels
        )

        geospatial_meta = GeospatialMetadata(
            has_georeference=post_out.geospatial_metadata["has_georeference"],
            crs=post_out.geospatial_metadata["crs"],
            bounds=post_out.geospatial_metadata["bounds"],
            affine_transform=post_out.geospatial_metadata["affine_transform"]
        )

        detection_files = DetectionFiles(
            original_image=original_url,
            segmentation_mask=mask_url,
            overlay=overlay_url,
            georeferenced_mask_tif=georef_url
        )

        manager = get_model_manager()
        total_time = round(inference_out.inference_time_seconds, 3)

        response = DetectionResponse(
            success=True,
            result_id=result_id,
            model=manager.repo_id,
            detection=detection_stats,
            geospatial=geospatial_meta,
            files=detection_files,
            processing_time_seconds=total_time
        )

        # 6. Save metadata JSON for retrieval
        meta_path = os.path.join(self.results_dir, f"meta_{result_id}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=2)

        return response

    def get_result_metadata(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis metadata by result_id."""
        meta_path = os.path.join(self.results_dir, f"meta_{result_id}.json")
        if not os.path.isfile(meta_path):
            return None
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_result_file_path(self, result_id: str, file_type: str) -> Optional[str]:
        """
        Retrieve absolute path for a generated result file.
        file_type: 'original', 'mask', 'overlay', 'geotiff'
        """
        mapping = {
            "original": f"original_{result_id}.png",
            "mask": f"mask_{result_id}.png",
            "overlay": f"overlay_{result_id}.png",
            "geotiff": f"georeferenced_mask_{result_id}.tif",
        }
        filename = mapping.get(file_type)
        if not filename:
            return None

        filepath = os.path.join(self.results_dir, filename)
        if not os.path.isfile(filepath):
            return None
        return filepath


satellite_service = SatelliteService()
