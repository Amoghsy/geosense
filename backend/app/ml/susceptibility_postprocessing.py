import os
import json
from typing import Optional, Dict, Any, List
import numpy as np
from PIL import Image

from app.ml.susceptibility_preprocessing import PreprocessedSusceptibilityData
from app.ml.susceptibility_inference import SusceptibilityInferenceResult
from app.utils.image_utils import percentile_stretch


def _create_rgb_preview_from_b4_b3_b2(raw_6band_chw: np.ndarray) -> Image.Image:
    """Create true-color RGB preview from [B4(Red), B3(Green), B2(Blue), ...]."""
    r = percentile_stretch(raw_6band_chw[0])
    g = percentile_stretch(raw_6band_chw[1])
    b = percentile_stretch(raw_6band_chw[2])
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")


def _create_terrain_preview(raw_6band_chw: np.ndarray) -> Image.Image:
    """Create false-color terrain preview from [B8(NIR), DEM, Slope]."""
    nir = percentile_stretch(raw_6band_chw[3])
    dem = percentile_stretch(raw_6band_chw[4])
    slope = percentile_stretch(raw_6band_chw[5])
    return Image.fromarray(np.stack([nir, dem, slope], axis=-1), mode="RGB")


def _build_geojson(
    preprocessed: PreprocessedSusceptibilityData,
    inference: SusceptibilityInferenceResult,
) -> Optional[Dict[str, Any]]:
    """Generate GeoJSON FeatureCollection ONLY when valid CRS and affine transform exist."""
    if not preprocessed.has_georeference or preprocessed.transform is None:
        return None

    t = preprocessed.transform
    features: List[Dict[str, Any]] = []

    for tile in inference.tile_scores:
        x0, x1 = tile["x_start"], tile["x_end"]
        y0, y1 = tile["y_start"], tile["y_end"]

        # Map pixel corners to geographic coordinates via affine transform
        top_left = t * (x0, y0)
        top_right = t * (x1, y0)
        bottom_right = t * (x1, y1)
        bottom_left = t * (x0, y1)

        coords = [
            [
                [float(top_left[0]), float(top_left[1])],
                [float(top_right[0]), float(top_right[1])],
                [float(bottom_right[0]), float(bottom_right[1])],
                [float(bottom_left[0]), float(bottom_left[1])],
                [float(top_left[0]), float(top_left[1])],
            ]
        ]

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": coords},
                "properties": {
                    "row": tile["row"],
                    "col": tile["col"],
                    "susceptibility_score": tile["susceptibility_score"],
                    "susceptibility_class": "Susceptible" if tile["is_susceptible"] else "Non-Susceptible",
                    "decision_threshold": inference.decision_threshold,
                    "crs": preprocessed.crs,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "crs_note": preprocessed.crs,
        "features": features,
    }


def postprocess_susceptibility_analysis(
    preprocessed: PreprocessedSusceptibilityData,
    inference: SusceptibilityInferenceResult,
    analysis_id: str,
    results_dir: str,
) -> Dict[str, str]:
    """Save RGB preview, terrain preview, and optional GeoJSON map to disk."""
    out_dir = os.path.join(results_dir, "susceptibility", analysis_id)
    os.makedirs(out_dir, exist_ok=True)

    rgb_path = os.path.join(out_dir, "rgb_preview.png")
    terrain_path = os.path.join(out_dir, "terrain_preview.png")

    _create_rgb_preview_from_b4_b3_b2(preprocessed.raw_6band_chw).save(rgb_path, format="PNG")
    _create_terrain_preview(preprocessed.raw_6band_chw).save(terrain_path, format="PNG")

    geojson_data = _build_geojson(preprocessed, inference)
    geojson_path = None
    if geojson_data is not None:
        geojson_path = os.path.join(out_dir, "susceptibility_map.geojson")
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

    return {
        "output_dir": out_dir,
        "rgb_path": rgb_path,
        "terrain_path": terrain_path,
        "geojson_path": geojson_path,
    }
