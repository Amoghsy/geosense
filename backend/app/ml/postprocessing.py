import os
import shutil
from typing import Dict, Any, Optional
from datetime import datetime, timezone
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
        total_valid_pixels: int,
        nodata_pixels: int,
        landslide_pixel_percentage: float,
        detected_area_percentage: float,
        original_image_path: str,
        mask_image_path: str,
        overlay_image_path: str,
        georeferenced_mask_path: Optional[str],
        detection_dir: str,
        geospatial_metadata: Dict[str, Any],
        image_dimensions: Dict[str, int]
    ):
        self.landslide_detected = landslide_detected
        self.landslide_pixels = landslide_pixels
        self.total_pixels = total_pixels
        self.total_valid_pixels = total_valid_pixels
        self.nodata_pixels = nodata_pixels
        self.landslide_pixel_percentage = landslide_pixel_percentage
        self.detected_area_percentage = detected_area_percentage
        self.original_image_path = original_image_path
        self.mask_image_path = mask_image_path
        self.overlay_image_path = overlay_image_path
        self.georeferenced_mask_path = georeferenced_mask_path
        self.detection_dir = detection_dir
        self.geospatial_metadata = geospatial_metadata
        self.image_dimensions = image_dimensions


def postprocess_landslide_detection(
    preprocessed: PreprocessedData,
    inference: InferenceResult,
    result_id: str,
    results_dir: str
) -> PostprocessingResult:
    """
    Generate output artifacts:
    1. RGB visual representation of original satellite bands
    2. Binary segmentation mask image (PNG)
    3. Colored overlay image highlighting landslides (PNG)
    4. Georeferenced mask GeoTIFF if CRS/transform are available
    5. Landslide pixel counts, valid pixel counts, nodata counts, and exact percentage
    6. Saves into structured directory results/detections/{result_id}/
    """
    detection_dir = os.path.join(results_dir, "detections", result_id)
    os.makedirs(detection_dir, exist_ok=True)

    mask = inference.mask_orig
    h, w = mask.shape
    total_pixels = int(mask.size)

    # Determine valid and nodata pixels accurately from valid_mask
    if preprocessed.valid_mask is not None:
        total_valid_pixels = int(np.count_nonzero(preprocessed.valid_mask))
        nodata_pixels = int(total_pixels - total_valid_pixels)
        # Ensure mask is 0 where invalid
        mask = np.where(preprocessed.valid_mask, mask, 0)
    else:
        total_valid_pixels = total_pixels
        nodata_pixels = 0

    landslide_pixels = int(np.count_nonzero(mask > 0))
    landslide_detected = landslide_pixels > 0
    landslide_percentage = round((landslide_pixels / total_valid_pixels) * 100.0, 4) if total_valid_pixels > 0 else 0.0

    # 1. RGB Preview
    rgb_img = create_rgb_preview(preprocessed.raw_bands_chw)
    structured_orig_path = os.path.join(detection_dir, "original.png")
    legacy_orig_path = os.path.join(results_dir, f"original_{result_id}.png")
    rgb_img.save(structured_orig_path, format="PNG")
    rgb_img.save(legacy_orig_path, format="PNG")

    # 2. Binary Mask Image
    structured_mask_path = os.path.join(detection_dir, "mask.png")
    legacy_mask_path = os.path.join(results_dir, f"mask_{result_id}.png")
    save_binary_mask_image(mask, structured_mask_path)
    save_binary_mask_image(mask, legacy_mask_path)

    # 3. Colored Overlay Image
    overlay_img = create_colored_overlay(rgb_img, mask)
    structured_overlay_path = os.path.join(detection_dir, "overlay.png")
    legacy_overlay_path = os.path.join(results_dir, f"overlay_{result_id}.png")
    overlay_img.save(structured_overlay_path, format="PNG")
    overlay_img.save(legacy_overlay_path, format="PNG")

    # 4. Georeferenced GeoTIFF Mask (if geospatial metadata is available)
    georef_filepath = None
    if preprocessed.has_georeference and preprocessed.crs and preprocessed.transform:
        structured_georef_path = os.path.join(detection_dir, "georeferenced_mask.tif")
        legacy_georef_path = os.path.join(results_dir, f"georeferenced_mask_{result_id}.tif")
        save_georeferenced_mask_tif(
            mask=mask,
            output_path=structured_georef_path,
            crs=preprocessed.crs,
            transform=preprocessed.transform
        )
        try:
            shutil.copy2(structured_georef_path, legacy_georef_path)
        except Exception:
            pass
        georef_filepath = structured_georef_path

    image_dimensions = {"width": int(w), "height": int(h)}

    geospatial_info = {
        "has_georeference": preprocessed.has_georeference,
        "crs": preprocessed.crs,
        "bounds": preprocessed.bounds,
        "affine_transform": list(preprocessed.transform) if preprocessed.transform else None,
        "image_dimensions": image_dimensions
    }

    return PostprocessingResult(
        landslide_detected=landslide_detected,
        landslide_pixels=landslide_pixels,
        total_pixels=total_pixels,
        total_valid_pixels=total_valid_pixels,
        nodata_pixels=nodata_pixels,
        landslide_pixel_percentage=landslide_percentage,
        detected_area_percentage=landslide_percentage,
        original_image_path=structured_orig_path,
        mask_image_path=structured_mask_path,
        overlay_image_path=structured_overlay_path,
        georeferenced_mask_path=georef_filepath,
        detection_dir=detection_dir,
        geospatial_metadata=geospatial_info,
        image_dimensions=image_dimensions
    )
