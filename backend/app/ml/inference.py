import time
import logging
from typing import Tuple, Dict, Any
import numpy as np
import torch
import cv2

from app.ml.model_loader import get_loaded_model, get_model_manager
from app.ml.preprocessing import PreprocessedData, TARGET_HEIGHT, TARGET_WIDTH

logger = logging.getLogger("geosense.inference")


class InferenceResult:
    def __init__(
        self,
        mask_224: np.ndarray,
        mask_orig: np.ndarray,
        landslide_prob_224: np.ndarray,
        landslide_prob_orig: np.ndarray,
        inference_time_seconds: float,
        is_tiled: bool = False
    ):
        self.mask_224 = mask_224  # Shape (224, 224) uint8 [0, 1]
        self.mask_orig = mask_orig  # Shape (orig_h, orig_w) uint8 [0, 1]
        self.landslide_prob_224 = landslide_prob_224  # Shape (224, 224) float32 [0.0, 1.0]
        self.landslide_prob_orig = landslide_prob_orig  # Shape (orig_h, orig_w) float32 [0.0, 1.0]
        self.inference_time_seconds = inference_time_seconds
        self.is_tiled = is_tiled


def _run_forward(model: torch.nn.Module, patch_tensor: torch.Tensor, device: torch.device) -> np.ndarray:
    """Run forward pass for a single (1, 6, 224, 224) tensor and return landslide probability (224, 224)."""
    with torch.no_grad():
        output = model(patch_tensor.to(device))
        if hasattr(output, "output"):
            logits = output.output
        elif isinstance(output, torch.Tensor):
            logits = output
        else:
            raise RuntimeError(f"Unexpected model output type: {type(output)}")

        probs = torch.softmax(logits, dim=1)
        return probs[0, 1, :, :].cpu().numpy().astype(np.float32)


def run_tiled_inference(
    model: torch.nn.Module,
    normalized_chw: np.ndarray,
    device: torch.device,
    tile_size: int = 224,
    stride: int = 160
) -> np.ndarray:
    """
    Perform sliding-window tiled inference across larger satellite rasters,
    blending overlapping boundaries using cosine/weighted accumulation.
    """
    c, h, w = normalized_chw.shape
    prob_canvas = np.zeros((h, w), dtype=np.float32)
    weight_canvas = np.zeros((h, w), dtype=np.float32)

    # 2D Hann window for smooth spatial boundary blending
    hann_1d = np.hanning(tile_size)
    window_2d = np.outer(hann_1d, hann_1d).astype(np.float32)
    window_2d = np.maximum(window_2d, 1e-4)

    y_steps = list(range(0, max(1, h - tile_size + 1), stride))
    if y_steps[-1] + tile_size < h:
        y_steps.append(h - tile_size)

    x_steps = list(range(0, max(1, w - tile_size + 1), stride))
    if x_steps[-1] + tile_size < w:
        x_steps.append(w - tile_size)

    for y in y_steps:
        for x in x_steps:
            patch = normalized_chw[:, y:y+tile_size, x:x+tile_size]
            # Handle edge if patch is smaller than tile_size
            ph, pw = patch.shape[1], patch.shape[2]
            if ph != tile_size or pw != tile_size:
                padded = np.zeros((c, tile_size, tile_size), dtype=np.float32)
                padded[:, :ph, :pw] = patch
                patch = padded

            patch_tensor = torch.from_numpy(patch).unsqueeze(0).float()
            patch_prob = _run_forward(model, patch_tensor, device)

            actual_window = window_2d[:ph, :pw]
            prob_canvas[y:y+ph, x:x+pw] += patch_prob[:ph, :pw] * actual_window
            weight_canvas[y:y+ph, x:x+pw] += actual_window

    weight_canvas = np.maximum(weight_canvas, 1e-6)
    return prob_canvas / weight_canvas


def run_landslide_inference(
    preprocessed: PreprocessedData,
    threshold: float = 0.5,
    enable_tiling: bool = True
) -> InferenceResult:
    """
    Run forward inference using the loaded Prithvi Landslide foundation model.
    Automatically applies tiled sliding-window inference for large satellite images (> 224x224).

    Args:
        preprocessed: PreprocessedData instance.
        threshold: Classification probability threshold for landslide class (default 0.5).
        enable_tiling: Whether to use sliding-window inference for images larger than 224x224.

    Returns:
        InferenceResult containing binary segmentation mask, probabilities, and latency.
    """
    manager = get_model_manager()
    model = manager.load_model()
    device = manager.device

    orig_h, orig_w = preprocessed.original_shape
    logger.info(f"Running inference on device: {device}, original dimensions: {orig_w}x{orig_h}")

    start_time = time.perf_counter()

    # Determine inference strategy based on dimensions
    is_tiled = False
    if enable_tiling and (orig_h > 224 or orig_w > 224):
        is_tiled = True
        logger.info(f"Using tiled sliding-window inference ({orig_w}x{orig_h})...")
        prob_orig = run_tiled_inference(model, preprocessed.normalized_full_chw, device)
        prob_224 = cv2.resize(prob_orig, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_LINEAR)
    else:
        logger.info("Using standard single-patch inference...")
        prob_224 = _run_forward(model, preprocessed.tensor, device)
        if (orig_h, orig_w) == (TARGET_HEIGHT, TARGET_WIDTH):
            prob_orig = prob_224.copy()
        else:
            prob_orig = cv2.resize(prob_224, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    inference_duration = time.perf_counter() - start_time
    logger.info(f"Inference completed in {inference_duration:.3f}s")

    # Generate binary mask using probability threshold
    mask_224 = (prob_224 >= threshold).astype(np.uint8)
    mask_orig = (prob_orig >= threshold).astype(np.uint8)

    # Strictly mask out NoData / invalid pixels
    if preprocessed.valid_mask is not None:
        mask_orig[~preprocessed.valid_mask] = 0

    return InferenceResult(
        mask_224=mask_224,
        mask_orig=mask_orig,
        landslide_prob_224=prob_224,
        landslide_prob_orig=prob_orig,
        inference_time_seconds=inference_duration,
        is_tiled=is_tiled
    )
