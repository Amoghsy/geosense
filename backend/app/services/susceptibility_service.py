import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import UploadFile

from app.ml.susceptibility_model_loader import get_susceptibility_model_manager
from app.ml.susceptibility_preprocessing import (
    preprocess_susceptibility_input,
    SusceptibilityValidationError,
)
from app.ml.susceptibility_inference import run_susceptibility_inference
from app.ml.susceptibility_postprocessing import postprocess_susceptibility_analysis
from app.db.database import save_susceptibility_analysis, get_susceptibility_analysis_record
from app.schemas.susceptibility_schema import (
    SusceptibilityAnalysisResponse,
    SusceptibilityPredictionOutput,
    SusceptibilityGeographicMetadata,
    SusceptibilityFiles,
)

logger = logging.getLogger("geosense.susceptibility_service")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
RESULTS_DIR = os.getenv("RESULT_DIR", os.path.join(BASE_DIR, "results"))

NE_INDIA_REGIONS: Dict[str, Dict[str, Any]] = {
    "meghalaya": {"name": "Meghalaya", "bbox": [89.8, 25.0, 92.8, 26.1]},
    "sikkim": {"name": "Sikkim", "bbox": [88.0, 27.0, 88.9, 28.15]},
    "assam": {"name": "Assam", "bbox": [89.7, 24.1, 96.0, 27.95]},
    "arunachal_pradesh": {"name": "Arunachal Pradesh", "bbox": [91.5, 26.6, 97.4, 29.5]},
    "manipur": {"name": "Manipur", "bbox": [93.0, 23.8, 94.8, 25.7]},
    "mizoram": {"name": "Mizoram", "bbox": [92.2, 21.9, 93.4, 24.5]},
    "nagaland": {"name": "Nagaland", "bbox": [93.3, 25.2, 95.25, 27.05]},
    "tripura": {"name": "Tripura", "bbox": [91.15, 22.9, 92.35, 24.55]},
}


class SusceptibilityService:
    def __init__(self):
        self.uploads_dir = os.path.abspath(UPLOADS_DIR)
        self.results_dir = os.path.abspath(RESULTS_DIR)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    async def analyze(
        self,
        file: UploadFile,
        region_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        data_source: Optional[str] = None,
    ) -> SusceptibilityAnalysisResponse:
        analysis_id = uuid.uuid4().hex[:12]
        safe_filename = os.path.basename(file.filename or "input.tif")
        upload_path = os.path.join(self.uploads_dir, f"phase2_{analysis_id}_{safe_filename}")

        contents = await file.read()
        if not contents:
            raise SusceptibilityValidationError("Uploaded file is empty.")

        with open(upload_path, "wb") as f:
            f.write(contents)

        # 1. Validate & preprocess multimodal 6-channel input
        preprocessed = preprocess_susceptibility_input(upload_path)

        # 2. Run actual model inference
        inference_out = run_susceptibility_inference(preprocessed)

        # 3. Postprocess previews and optional GeoJSON map
        artifacts = postprocess_susceptibility_analysis(
            preprocessed=preprocessed,
            inference=inference_out,
            analysis_id=analysis_id,
            results_dir=self.results_dir,
        )

        # 4. Geographic association & coverage checks for North Eastern India
        warnings: List[str] = list(preprocessed.warnings)
        region_key = region_id.lower().strip() if region_id else None
        region_info = NE_INDIA_REGIONS.get(region_key) if region_key else None
        region_name = region_info["name"] if region_info else region_id

        # Derive center coordinates from GeoTIFF bounds if not explicitly provided
        eff_lat = latitude
        eff_lon = longitude
        if (eff_lat is None or eff_lon is None) and preprocessed.bounds and "4326" in str(preprocessed.crs):
            eff_lat = round((preprocessed.bounds["bottom"] + preprocessed.bounds["top"]) / 2.0, 6)
            eff_lon = round((preprocessed.bounds["left"] + preprocessed.bounds["right"]) / 2.0, 6)

        coverage_status = "uncalibrated_prototype"
        coverage_limitations = (
            "vinukatashidu/landslide-detection-multimodal is an experimental academic model "
            "not specifically calibrated or field-validated across all 8 states of North Eastern India. "
            "Results represent static visual+terrain susceptibility scores only and omit live rainfall/seismic triggers."
        )
        warnings.append(
            "Model coverage notice: Pretrained weights are not locally calibrated for North Eastern India terrain."
        )

        manager = get_susceptibility_model_manager()
        created_at = datetime.now(timezone.utc).isoformat()

        prediction_out = SusceptibilityPredictionOutput(
            raw_logit=inference_out.raw_logit,
            susceptibility_score=inference_out.susceptibility_score,
            decision_threshold=inference_out.decision_threshold,
            is_susceptible=inference_out.is_susceptible,
            susceptibility_class=inference_out.susceptibility_class,
            tile_count=inference_out.tile_count,
            tile_scores=inference_out.tile_scores,
        )

        geographic_meta = SusceptibilityGeographicMetadata(
            region_id=region_key,
            region_name=region_name,
            latitude=eff_lat,
            longitude=eff_lon,
            has_georeference=preprocessed.has_georeference,
            crs=preprocessed.crs,
            bounds=preprocessed.bounds,
            image_dimensions={
                "width": preprocessed.original_shape[1],
                "height": preprocessed.original_shape[0],
            },
            coverage_status=coverage_status,
            coverage_limitations=coverage_limitations,
        )

        source_metadata = {
            "uploaded_filename": safe_filename,
            "declared_data_source": data_source or "User-supplied Sentinel-2 + SRTM DEM/Slope raster",
            "ingestion_timestamp": created_at,
        }

        files_out = SusceptibilityFiles(
            rgb_preview=f"/susceptibility/analyze/{analysis_id}/preview/rgb",
            terrain_preview=f"/susceptibility/analyze/{analysis_id}/preview/terrain",
            geojson_map=f"/susceptibility/analyze/{analysis_id}/map" if artifacts["geojson_path"] else None,
            metadata_json=f"/susceptibility/analyze/{analysis_id}/metadata",
        )

        response = SusceptibilityAnalysisResponse(
            success=True,
            analysis_id=analysis_id,
            model_repository=manager.repo_id,
            model_revision=manager.revision,
            prediction=prediction_out,
            geographic=geographic_meta,
            input_metadata=preprocessed.input_metadata,
            source_metadata=source_metadata,
            data_quality_warnings=warnings,
            files=files_out,
            processing_time_seconds=inference_out.inference_time_seconds,
            created_at=created_at,
        )

        # Save result.json
        result_json_path = os.path.join(artifacts["output_dir"], "result.json")
        with open(result_json_path, "w", encoding="utf-8") as f:
            json.dump(response.model_dump(), f, indent=2)

        # Persist in SQLite database
        save_susceptibility_analysis(
            {
                "id": analysis_id,
                "region_id": region_key,
                "latitude": eff_lat,
                "longitude": eff_lon,
                "input_metadata": preprocessed.input_metadata,
                "model_repository": manager.repo_id,
                "model_revision": manager.revision,
                "prediction_output": prediction_out.model_dump(),
                "susceptibility_value": inference_out.susceptibility_score,
                "susceptibility_class": inference_out.susceptibility_class,
                "confidence": inference_out.susceptibility_score,
                "source_metadata": source_metadata,
                "coverage_status": coverage_status,
                "processing_time": inference_out.inference_time_seconds,
                "created_at": created_at,
            }
        )

        return response

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        json_path = os.path.join(self.results_dir, "susceptibility", analysis_id, "result.json")
        if os.path.isfile(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return get_susceptibility_analysis_record(analysis_id)

    def get_artifact_path(self, analysis_id: str, artifact: str) -> Optional[str]:
        base = os.path.join(self.results_dir, "susceptibility", analysis_id)
        mapping = {
            "rgb": os.path.join(base, "rgb_preview.png"),
            "terrain": os.path.join(base, "terrain_preview.png"),
            "map": os.path.join(base, "susceptibility_map.geojson"),
            "metadata": os.path.join(base, "result.json"),
        }
        path = mapping.get(artifact)
        if path and os.path.isfile(path):
            return path
        return None


susceptibility_service = SusceptibilityService()
