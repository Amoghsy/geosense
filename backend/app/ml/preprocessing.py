import os
from typing import Dict, Any, Tuple, Optional
import numpy as np
import torch
import cv2
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine
import h5py


# Exact TerraTorch Landslide4Sense normalization constants
PRITHVI_BANDS = ["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"]
LANDSLIDE4SENSE_14_BANDS = [
    "COASTAL AEROSOL", "BLUE", "GREEN", "RED", "RED_EDGE_1", "RED_EDGE_2",
    "RED_EDGE_3", "NIR_BROAD", "WATER_VAPOR", "CIRRUS", "SWIR_1", "SWIR_2",
    "SLOPE", "DEM"
]

BAND_MEANS = {
    "BLUE": -0.3074,
    "GREEN": -0.1277,
    "RED": -0.0625,
    "NIR_BROAD": 0.0802,
    "SWIR_1": 0.0823,
    "SWIR_2": 0.0516
}

BAND_STDS = {
    "BLUE": 0.8775,
    "GREEN": 0.8860,
    "RED": 0.8869,
    "NIR_BROAD": 0.8491,
    "SWIR_1": 0.8848,
    "SWIR_2": 0.9232
}

TARGET_HEIGHT = 224
TARGET_WIDTH = 224


class SatelliteValidationError(ValueError):
    """Raised when an uploaded file fails satellite validation."""
    pass


class PreprocessedData:
    def __init__(
        self,
        tensor: torch.Tensor,
        raw_bands_chw: np.ndarray,
        normalized_full_chw: np.ndarray,
        valid_mask: np.ndarray,
        original_shape: Tuple[int, int],
        has_georeference: bool,
        crs: Optional[str] = None,
        transform: Optional[Affine] = None,
        bounds: Optional[Dict[str, float]] = None,
        nodata_val: Optional[float] = None
    ):
        self.tensor = tensor  # Resized tensor: (1, 6, 224, 224)
        self.raw_bands_chw = raw_bands_chw  # Shape: (6, H, W)
        self.normalized_full_chw = normalized_full_chw  # Shape: (6, H, W)
        self.valid_mask = valid_mask  # Shape: (H, W) boolean
        self.original_shape = original_shape  # (H, W)
        self.has_georeference = has_georeference
        self.crs = crs
        self.transform = transform
        self.bounds = bounds
        self.nodata_val = nodata_val


def read_geotiff(file_path: str) -> Tuple[np.ndarray, np.ndarray, bool, Optional[str], Optional[Affine], Optional[Dict[str, float]], Optional[float]]:
    """
    Read satellite GeoTIFF file, extracting multi-band raster, valid data mask, and geospatial metadata.
    """
    try:
        with rasterio.open(file_path) as src:
            band_count = src.count
            height = src.height
            width = src.width
            nodata_val = src.nodata

            if band_count == 3:
                raise SatelliteValidationError(
                    "Standard 3-band RGB photograph detected. The Prithvi Landslide model is a multispectral "
                    "foundation model that strictly requires 6 satellite bands (BLUE, GREEN, RED, NIR_BROAD, SWIR_1, SWIR_2). "
                    "Ordinary mobile/camera photographs and 3-band RGB images are not valid satellite inputs."
                )

            if band_count not in (6, 14):
                raise SatelliteValidationError(
                    f"Unsupported number of bands: {band_count}. Input satellite image must have either 6 bands "
                    f"(BLUE, GREEN, RED, NIR_BROAD, SWIR_1, SWIR_2) or 14 bands (Landslide4Sense benchmark format)."
                )

            data = src.read()  # Shape: (bands, H, W)

            if band_count == 14:
                # Landslide4Sense indices: BLUE=1, GREEN=2, RED=3, NIR_BROAD=7, SWIR_1=10, SWIR_2=11
                indices = [1, 2, 3, 7, 10, 11]
                data = data[indices, :, :]

            # Compute valid pixel mask (exclude NoData, NaNs, and Infs)
            valid_mask = np.ones((height, width), dtype=bool)
            for b in range(data.shape[0]):
                finite_b = np.isfinite(data[b])
                valid_mask &= finite_b
                if nodata_val is not None and not np.isnan(nodata_val):
                    valid_mask &= (data[b] != nodata_val)

            # Check if any band has completely empty or invalid data
            for idx, band_name in enumerate(PRITHVI_BANDS):
                if not np.any(np.isfinite(data[idx])):
                    raise SatelliteValidationError(
                        f"Missing spectral data: Band {band_name} (index {idx}) contains no finite valid pixels."
                    )

            if not np.any(valid_mask):
                raise SatelliteValidationError("Uploaded satellite image contains only NoData or empty pixels.")

            has_georef = bool(src.crs is not None and src.transform is not None)
            crs_str = str(src.crs) if src.crs else None
            transform = src.transform if has_georef else None
            bounds = None
            if has_georef and src.bounds:
                bounds = {
                    "left": float(src.bounds.left),
                    "bottom": float(src.bounds.bottom),
                    "right": float(src.bounds.right),
                    "top": float(src.bounds.top),
                }

            return data.astype(np.float32), valid_mask, has_georef, crs_str, transform, bounds, nodata_val

    except rasterio.RasterioIOError as e:
        raise SatelliteValidationError(f"Invalid or corrupted GeoTIFF file: {str(e)}")


def read_hdf5(file_path: str) -> Tuple[np.ndarray, np.ndarray, bool, Optional[str], Optional[Affine], Optional[Dict[str, float]], Optional[float]]:
    """
    Read satellite HDF5 file (Landslide4Sense benchmark format).
    """
    try:
        with h5py.File(file_path, "r") as h5f:
            if "img" not in h5f:
                raise SatelliteValidationError(
                    f"HDF5 file must contain dataset 'img'. Available keys: {list(h5f.keys())}"
                )
            img = np.array(h5f["img"])  # Expected shape (H, W, C)

            if img.ndim != 3:
                raise SatelliteValidationError(
                    f"Expected 3-dimensional array (H, W, Channels) in HDF5 'img', got shape {img.shape}"
                )

            channels = img.shape[-1]
            if channels == 14:
                indices = [1, 2, 3, 7, 10, 11]
                selected = img[..., indices]
            elif channels == 6:
                selected = img
            elif channels == 3:
                raise SatelliteValidationError(
                    "Standard 3-band RGB image detected in HDF5. Multispectral 6-band satellite imagery is required."
                )
            else:
                raise SatelliteValidationError(
                    f"Invalid number of channels in HDF5: {channels}. Expected 6 or 14 bands."
                )

            # Move channel to first dimension: (C, H, W)
            chw = np.moveaxis(selected, -1, 0).astype(np.float32)
            h, w = chw.shape[1], chw.shape[2]

            valid_mask = np.ones((h, w), dtype=bool)
            for b in range(chw.shape[0]):
                valid_mask &= np.isfinite(chw[b])

            if not np.any(valid_mask):
                raise SatelliteValidationError("Uploaded HDF5 dataset contains only NoData or empty pixels.")

            return chw, valid_mask, False, None, None, None, None

    except Exception as e:
        if isinstance(e, SatelliteValidationError):
            raise
        raise SatelliteValidationError(f"Invalid HDF5 satellite file: {str(e)}")


def normalize_bands(bands_chw: np.ndarray) -> np.ndarray:
    """
    Apply exact per-band z-score normalization expected by the fine-tuned Prithvi model.
    Formula: (x - mean) / std for each band.
    """
    normed = np.zeros_like(bands_chw, dtype=np.float32)
    for idx, band_name in enumerate(PRITHVI_BANDS):
        m = BAND_MEANS[band_name]
        s = BAND_STDS[band_name]
        normed[idx] = (bands_chw[idx] - m) / s
    return normed


def resize_multispectral_chw(bands_chw: np.ndarray, target_h: int = TARGET_HEIGHT, target_w: int = TARGET_WIDTH) -> np.ndarray:
    """
    Resize 6-band CHW array to target dimensions using bilinear interpolation per band.
    """
    c, h, w = bands_chw.shape
    if h == target_h and w == target_w:
        return bands_chw

    resized = np.zeros((c, target_h, target_w), dtype=np.float32)
    for idx in range(c):
        resized[idx] = cv2.resize(bands_chw[idx], (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    return resized


def preprocess_satellite_image(file_path: str) -> PreprocessedData:
    """
    Validate, load, normalize, and prepare an uploaded satellite image for Prithvi inference.
    Rejects ordinary photos and unsupported file types.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".tif", ".tiff"]:
        raw_bands_chw, valid_mask, has_georef, crs_str, transform, bounds, nodata_val = read_geotiff(file_path)
    elif ext in [".h5", ".hdf5"]:
        raw_bands_chw, valid_mask, has_georef, crs_str, transform, bounds, nodata_val = read_hdf5(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise SatelliteValidationError(
            f"Unsupported file format '{ext}'. Standard photographic images (JPEG/PNG) cannot provide "
            "the 6 multispectral satellite bands (BLUE, GREEN, RED, NIR_BROAD, SWIR_1, SWIR_2) required by the "
            "Prithvi foundation model. Please upload a multispectral GeoTIFF (.tif) or HDF5 (.h5) file."
        )
    else:
        raise SatelliteValidationError(
            f"Unsupported file extension '{ext}'. Only multispectral GeoTIFF (.tif, .tiff) and HDF5 (.h5, .hdf5) "
            "satellite files are supported."
        )

    # Validate shape
    if raw_bands_chw.ndim != 3 or raw_bands_chw.shape[0] != 6:
        raise SatelliteValidationError(f"Expected 6 bands, got shape {raw_bands_chw.shape}")

    c, orig_h, orig_w = raw_bands_chw.shape
    if orig_h < 16 or orig_w < 16:
        raise SatelliteValidationError(f"Image dimensions too small ({orig_h}x{orig_w}). Minimum size is 16x16.")

    # Replace NaNs or Infs if any with 0.0 for clean normalization
    clean_bands_chw = np.nan_to_num(raw_bands_chw, nan=0.0, posinf=0.0, neginf=0.0)

    # Normalize bands with documented constants
    normalized_full_chw = normalize_bands(clean_bands_chw)

    # Resize to model input dimensions (224, 224) for single-patch inference
    resized_normed = resize_multispectral_chw(normalized_full_chw, TARGET_HEIGHT, TARGET_WIDTH)

    # Convert to PyTorch Tensor with batch dimension (1, 6, 224, 224)
    tensor = torch.from_numpy(resized_normed).unsqueeze(0).float()

    return PreprocessedData(
        tensor=tensor,
        raw_bands_chw=clean_bands_chw,
        normalized_full_chw=normalized_full_chw,
        valid_mask=valid_mask,
        original_shape=(orig_h, orig_w),
        has_georeference=has_georef,
        crs=crs_str,
        transform=transform,
        bounds=bounds,
        nodata_val=nodata_val
    )
