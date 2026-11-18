import os
from typing import Dict, Any, Optional
import numpy as np

from app.ml.preprocessing import PreprocessedData
from app.ml.inference import InferenceResult
from app.utils.image_utils import (
    create_rgb_preview,
    create_colored_overlay,
    save_binary_mask_image,
    save_georeferenced_mask_tif
)


class PostprocessingResult:
    def __init__(
        self,
        landslide_detected: bool,
        landslide_pixels: int,
        total_pixels: int,
        landslide_pixel_percentage: float,
        original_image_path: str,
        mask_image_path: str,
        overlay_image_path: str,
        georeferenced_mask_path: Optional[str],
        geospatial_metadata: Dict[str, Any]
    ):
        self.landslide_detected = landslide_detected
        self.landslide_pixels = landslide_pixels
        self.total_pixels = total_pixels
        self.landslide_pixel_percentage = landslide_pixel_percentage
        self.original_image_path = original_image_path
        self.mask_image_path = mask_image_path
        self.overlay_image_path = overlay_image_path
        self.georeferenced_mask_path = georeferenced_mask_path
        self.geospatial_metadata = geospatial_metadata


def postprocess_landslide_detection(
    preprocessed: PreprocessedData,
    inference: InferenceResult,
    result_id: str,
    results_dir: str
) -> PostprocessingResult:
    """
    Generate output artifacts:
    1. RGB visual representation of original satellite bands
    2. Binary segmentation mask image
    3. Colored overlay image highlighting landslides
    4. Georeferenced mask GeoTIFF if CRS/transform are available
    5. Landslide pixel counts and percentage
    """
    os.makedirs(results_dir, exist_ok=True)

    mask = inference.mask_orig
    total_pixels = int(mask.size)
    landslide_pixels = int(np.count_nonzero(mask > 0))
    landslide_detected = landslide_pixels > 0
    landslide_percentage = round((landslide_pixels / total_pixels) * 100.0, 2) if total_pixels > 0 else 0.0

    # 1. RGB Preview
    rgb_img = create_rgb_preview(preprocessed.raw_bands_chw)
    original_filename = f"original_{result_id}.png"
    original_filepath = os.path.join(results_dir, original_filename)
    rgb_img.save(original_filepath, format="PNG")

    # 2. Binary Mask Image
    mask_filename = f"mask_{result_id}.png"
    mask_filepath = os.path.join(results_dir, mask_filename)
    save_binary_mask_image(mask, mask_filepath)

    # 3. Colored Overlay Image
    overlay_img = create_colored_overlay(rgb_img, mask)
    overlay_filename = f"overlay_{result_id}.png"
    overlay_filepath = os.path.join(results_dir, overlay_filename)
    overlay_img.save(overlay_filepath, format="PNG")

    # 4. Georeferenced GeoTIFF Mask (if geospatial metadata is available)
    georef_filename = None
    georef_filepath = None
    if preprocessed.has_georeference and preprocessed.crs and preprocessed.transform:
        georef_filename = f"georeferenced_mask_{result_id}.tif"
        georef_filepath = os.path.join(results_dir, georef_filename)
        save_georeferenced_mask_tif(
            mask=mask,
            output_path=georef_filepath,
            crs=preprocessed.crs,
            transform=preprocessed.transform
        )

    geospatial_info = {
        "has_georeference": preprocessed.has_georeference,
        "crs": preprocessed.crs,
        "bounds": preprocessed.bounds,
        "affine_transform": list(preprocessed.transform) if preprocessed.transform else None
    }

    return PostprocessingResult(
        landslide_detected=landslide_detected,
        landslide_pixels=landslide_pixels,
        total_pixels=total_pixels,
        landslide_pixel_percentage=landslide_percentage,
        original_image_path=original_filepath,
        mask_image_path=mask_filepath,
        overlay_image_path=overlay_filepath,
        georeferenced_mask_path=georef_filepath,
        geospatial_metadata=geospatial_info
    )
