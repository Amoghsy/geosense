import os
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List

import numpy as np
import torch
import cv2
import rasterio
from rasterio.transform import Affine

REQUIRED_CHANNELS = ["B4 (Red)", "B3 (Green)", "B2 (Blue)", "B8 (NIR)", "DEM", "Slope"]
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)

SUPPORTED_EXTENSIONS = {".tif", ".tiff", ".npy"}
REJECTED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class SusceptibilityValidationError(Exception):
    """Raised when Phase 2 multimodal input data fails validation."""
    pass


@dataclass
class PreprocessedSusceptibilityData:
    rgb_tensor_chw: np.ndarray        # (3, H, W) ImageNet-normalized float32
    terrain_tensor_chw: np.ndarray    # (3, H, W) [0, 1] normalized float32
    raw_6band_chw: np.ndarray         # (6, H, W) original float32 for visualization
    original_shape: Tuple[int, int]   # (H, W)
    has_georeference: bool
    crs: Optional[str]
    transform: Optional[Affine]
    bounds: Optional[Dict[str, float]]
    input_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def _normalize_rgb_and_terrain(
    bands_chw: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, List[str], Dict[str, Any]]:
    """
    Normalize 6-band [B4, B3, B2, B8, DEM, Slope] strictly following
    vinukatashidu/landslide-detection-multimodal (10_train_multimodal_pytorch.py):
    - RGB [B4, B3, B2]: scaled to [0, 1], then ImageNet normalized.
    - Terrain [B8, DEM, Slope]: normalized to [0, 1] using (5000, 3000m, 90 deg) if raw physical units.
    """
    warnings: List[str] = []
    scaling_info: Dict[str, str] = {}

    rgb = bands_chw[0:3].astype(np.float32)
    terrain = bands_chw[3:6].astype(np.float32)

    # Validate finite values per channel
    for idx, name in enumerate(REQUIRED_CHANNELS):
        ch = bands_chw[idx]
        if not np.any(np.isfinite(ch)):
            raise SusceptibilityValidationError(
                f"Channel {idx} ({name}) contains no finite valid pixels."
            )

    # Replace isolated NaNs with channel median for inference stability while warning user
    nan_count = int(np.count_nonzero(~np.isfinite(bands_chw)))
    if nan_count > 0:
        warnings.append(
            f"Input contained {nan_count} non-finite (NaN/Inf) pixels across 6 channels; "
            "imputed with per-channel median for patch evaluation."
        )
        for c in range(3):
            if not np.all(np.isfinite(rgb[c])):
                med = float(np.nanmedian(rgb[c]))
                rgb[c] = np.where(np.isfinite(rgb[c]), rgb[c], med)
            if not np.all(np.isfinite(terrain[c])):
                med = float(np.nanmedian(terrain[c]))
                terrain[c] = np.where(np.isfinite(terrain[c]), terrain[c], med)

    # RGB scaling to [0, 1]
    rgb_max = float(np.max(rgb))
    rgb_min = float(np.min(rgb))
    if rgb_min < 0.0:
        warnings.append("Negative reflectance values in RGB bands were clipped to 0.0.")
        rgb = np.clip(rgb, 0.0, None)

    if rgb_max <= 1.05:
        rgb_01 = np.clip(rgb, 0.0, 1.0)
        scaling_info["rgb"] = "already [0, 1]"
    elif rgb_max <= 255.0:
        rgb_01 = np.clip(rgb / 255.0, 0.0, 1.0)
        scaling_info["rgb"] = "scaled from [0, 255] to [0, 1]"
    else:
        rgb_01 = np.clip(rgb / 10000.0, 0.0, 1.0)
        scaling_info["rgb"] = "scaled from Sentinel-2 DN [0, 10000] to [0, 1]"

    rgb_norm = (rgb_01 - IMAGENET_MEAN) / IMAGENET_STD

    # Terrain normalization: B8 (0-5000), DEM (0-3000m), Slope (0-90 deg)
    b8 = terrain[0]
    dem = terrain[1]
    slope = terrain[2]

    if float(np.max(b8)) <= 1.05 and float(np.min(b8)) >= 0.0:
        b8_norm = np.clip(b8, 0.0, 1.0)
        scaling_info["B8_NIR"] = "already [0, 1]"
    else:
        b8_norm = np.clip(b8 / 5000.0, 0.0, 1.0)
        scaling_info["B8_NIR"] = "normalized by 5000 reflectance"

    if float(np.max(dem)) <= 1.05 and float(np.min(dem)) >= 0.0:
        dem_norm = np.clip(dem, 0.0, 1.0)
        scaling_info["DEM"] = "already [0, 1]"
    else:
        dem_norm = np.clip(dem / 3000.0, 0.0, 1.0)
        scaling_info["DEM"] = "normalized by 3000m elevation"

    if float(np.max(slope)) <= 1.05 and float(np.min(slope)) >= 0.0:
        slope_norm = np.clip(slope, 0.0, 1.0)
        scaling_info["Slope"] = "already [0, 1]"
    else:
        slope_norm = np.clip(slope / 90.0, 0.0, 1.0)
        scaling_info["Slope"] = "normalized by 90 degrees"

    terrain_norm = np.stack([b8_norm, dem_norm, slope_norm], axis=0).astype(np.float32)
    return rgb_norm.astype(np.float32), terrain_norm, warnings, scaling_info


def preprocess_susceptibility_input(file_path: str) -> PreprocessedSusceptibilityData:
    """
    Validate and preprocess 6-channel multimodal input (.tif/.tiff or .npy).
    Strictly rejects standard 3-band RGB photos and never fabricates missing terrain channels.
    """
    if not os.path.isfile(file_path):
        raise SusceptibilityValidationError(f"Input file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext in REJECTED_PHOTO_EXTENSIONS:
        raise SusceptibilityValidationError(
            f"Standard photographic images ('{ext}') are not supported for Phase 2 susceptibility analysis. "
            "The model strictly requires 6 multimodal channels: [B4, B3, B2, B8 (NIR), DEM, Slope]. "
            "Missing NIR, DEM, and Slope data cannot be fabricated."
        )

    if ext not in SUPPORTED_EXTENSIONS:
        raise SusceptibilityValidationError(
            f"Unsupported file extension '{ext}'. Supported formats: GeoTIFF (.tif, .tiff) and NumPy (.npy)."
        )

    has_georeference = False
    crs_str: Optional[str] = None
    transform: Optional[Affine] = None
    bounds_dict: Optional[Dict[str, float]] = None

    if ext in {".tif", ".tiff"}:
        try:
            with rasterio.open(file_path) as src:
                count = src.count
                height, width = src.height, src.width
                if count == 3:
                    raise SusceptibilityValidationError(
                        "3-band RGB GeoTIFF detected. Phase 2 requires 6 channels: "
                        "[B4 (Red), B3 (Green), B2 (Blue), B8 (NIR), DEM, Slope]. "
                        "Missing NIR, DEM, and Slope channels cannot be fabricated."
                    )
                if count != 6:
                    raise SusceptibilityValidationError(
                        f"Unsupported band count: {count}. Expected exactly 6 bands: {REQUIRED_CHANNELS}."
                    )
                if height < 32 or width < 32:
                    raise SusceptibilityValidationError(
                        f"Image dimensions ({width}x{height}) are too small. Minimum supported size is 32x32."
                    )
                raw_bands = src.read().astype(np.float32)

                if src.crs is not None:
                    has_georeference = True
                    crs_str = str(src.crs)
                    transform = src.transform
                    b = src.bounds
                    bounds_dict = {
                        "left": float(b.left),
                        "bottom": float(b.bottom),
                        "right": float(b.right),
                        "top": float(b.top),
                    }
        except SusceptibilityValidationError:
            raise
        except Exception as exc:
            raise SusceptibilityValidationError(f"Failed to read GeoTIFF raster: {exc}") from exc
    else:
        # .npy format (matching repository's dataset_proposed .npy format)
        try:
            arr = np.load(file_path)
        except Exception as exc:
            raise SusceptibilityValidationError(f"Failed to load NumPy array: {exc}") from exc

        if arr.ndim != 3:
            raise SusceptibilityValidationError(
                f"Expected 3D array (6, H, W) in .npy file, got shape {arr.shape}."
            )
        if arr.shape[0] != 6:
            raise SusceptibilityValidationError(
                f"Expected 6 channels in axis 0 for .npy file, got shape {arr.shape}. "
                f"Required channels: {REQUIRED_CHANNELS}."
            )
        raw_bands = arr.astype(np.float32)
        height, width = raw_bands.shape[1], raw_bands.shape[2]
        if height < 32 or width < 32:
            raise SusceptibilityValidationError(
                f"Array dimensions ({width}x{height}) are too small. Minimum supported size is 32x32."
            )

    rgb_norm, terrain_norm, warnings, scaling_info = _normalize_rgb_and_terrain(raw_bands)
    if not has_georeference:
        warnings.append(
            "Input lacks geospatial CRS/transform metadata; geographic map projection cannot be generated."
        )

    input_metadata = {
        "file_format": ext,
        "channels": REQUIRED_CHANNELS,
        "original_dimensions": {"width": int(width), "height": int(height)},
        "scaling_applied": scaling_info,
    }

    return PreprocessedSusceptibilityData(
        rgb_tensor_chw=rgb_norm,
        terrain_tensor_chw=terrain_norm,
        raw_6band_chw=raw_bands,
        original_shape=(int(height), int(width)),
        has_georeference=has_georeference,
        crs=crs_str,
        transform=transform,
        bounds=bounds_dict,
        input_metadata=input_metadata,
        warnings=warnings,
    )
