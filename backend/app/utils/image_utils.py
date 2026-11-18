import os
from typing import Tuple, Optional, Dict, Any
import numpy as np
from PIL import Image
import cv2
import rasterio
from rasterio.transform import Affine


def percentile_stretch(channel: np.ndarray, lower_percentile: float = 2.0, upper_percentile: float = 98.0) -> np.ndarray:
    """Apply percentile stretching to satellite band for visual display."""
    valid_mask = np.isfinite(channel)
    if not np.any(valid_mask):
        return np.zeros_like(channel, dtype=np.uint8)

    p_low = np.percentile(channel[valid_mask], lower_percentile)
    p_high = np.percentile(channel[valid_mask], upper_percentile)

    if p_high - p_low < 1e-6:
        stretched = np.zeros_like(channel)
    else:
        stretched = np.clip((channel - p_low) / (p_high - p_low), 0.0, 1.0)

    return (stretched * 255.0).astype(np.uint8)


def create_rgb_preview(bands_chw: np.ndarray) -> Image.Image:
    """
    Generate an RGB visualization from 6-band satellite imagery.
    Assumes bands ordering: [BLUE, GREEN, RED, NIR_BROAD, SWIR_1, SWIR_2].
    Index 2 is RED, Index 1 is GREEN, Index 0 is BLUE.
    """
    if bands_chw.shape[0] < 3:
        raise ValueError(f"Expected at least 3 bands for RGB rendering, got {bands_chw.shape[0]}")

    # True Color: R=Red(idx 2), G=Green(idx 1), B=Blue(idx 0)
    red_band = bands_chw[2]
    green_band = bands_chw[1]
    blue_band = bands_chw[0]

    r_vis = percentile_stretch(red_band)
    g_vis = percentile_stretch(green_band)
    b_vis = percentile_stretch(blue_band)

    rgb = np.stack([r_vis, g_vis, b_vis], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def create_colored_overlay(
    rgb_image: Image.Image,
    mask: np.ndarray,
    overlay_color: Tuple[int, int, int] = (255, 30, 30),  # Bright Red/Crimson
    alpha: float = 0.55
) -> Image.Image:
    """
    Generate a colored semi-transparent overlay highlighting landslide regions on the base satellite image.
    rgb_image: PIL Image of RGB satellite preview.
    mask: 2D numpy array with 0 (non-landslide) and 1 (landslide).
    """
    base_np = np.array(rgb_image).copy()
    h, w = base_np.shape[:2]

    # Resize mask to base image dimensions if needed
    if mask.shape != (h, w):
        mask = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)

    overlay = base_np.copy()
    landslide_pixels = mask > 0

    if np.any(landslide_pixels):
        overlay[landslide_pixels] = overlay_color
        # Blend only where landslide pixels are detected
        blended = cv2.addWeighted(overlay, alpha, base_np, 1 - alpha, 0)
        # Keep non-landslide pixels identical to original
        result = np.where(landslide_pixels[:, :, None], blended, base_np)

        # Highlight boundary edges with subtle bright contour
        mask_uint8 = (landslide_pixels * 255).astype(np.uint8)
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, (255, 230, 0), thickness=1)  # Yellow outline
    else:
        result = base_np

    return Image.fromarray(result, mode="RGB")


def save_binary_mask_image(mask: np.ndarray, filepath: str) -> None:
    """Save binary mask as 8-bit black/white PNG (0=background, 255=landslide)."""
    mask_vis = (np.clip(mask, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(mask_vis, mode="L")
    img.save(filepath, format="PNG")


def save_georeferenced_mask_tif(
    mask: np.ndarray,
    output_path: str,
    crs: Any,
    transform: Affine
) -> None:
    """
    Save the segmentation mask as a georeferenced single-band GeoTIFF raster.
    """
    h, w = mask.shape
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=1,
        dtype=np.uint8,
        crs=crs,
        transform=transform,
        nodata=255
    ) as dst:
        dst.write(mask.astype(np.uint8), 1)
        dst.set_band_description(1, "Landslide Detection Mask (0=No Landslide, 1=Landslide)")
