import time
from typing import Tuple, Dict, Any
import numpy as np
import torch
import cv2

from app.ml.model_loader import get_loaded_model, get_model_manager
from app.ml.preprocessing import PreprocessedData


class InferenceResult:
    def __init__(
        self,
        mask_224: np.ndarray,
        mask_orig: np.ndarray,
        landslide_prob_224: np.ndarray,
        landslide_prob_orig: np.ndarray,
        inference_time_seconds: float
    ):
        self.mask_224 = mask_224  # Shape (224, 224) uint8 [0, 1]
        self.mask_orig = mask_orig  # Shape (orig_h, orig_w) uint8 [0, 1]
        self.landslide_prob_224 = landslide_prob_224  # Shape (224, 224) float32 [0.0, 1.0]
        self.landslide_prob_orig = landslide_prob_orig  # Shape (orig_h, orig_w) float32 [0.0, 1.0]
        self.inference_time_seconds = inference_time_seconds


def run_landslide_inference(
    preprocessed: PreprocessedData,
    threshold: float = 0.5
) -> InferenceResult:
    """
    Run forward inference using the loaded Prithvi Landslide foundation model.

    Args:
        preprocessed: PreprocessedData instance containing (1, 6, 224, 224) normalized tensor.
        threshold: Classification probability threshold for landslide class (default 0.5).

    Returns:
        InferenceResult containing binary segmentation mask, probabilities, and latency.
    """
    manager = get_model_manager()
    model = manager.load_model()
    device = manager.device

    input_tensor = preprocessed.tensor.to(device)

    start_time = time.perf_counter()
    with torch.no_grad():
        output = model(input_tensor)

        # Output is either a ModelOutput object with an .output attribute, or a raw Tensor
        if hasattr(output, "output"):
            logits = output.output
        elif isinstance(output, torch.Tensor):
            logits = output
        else:
            raise RuntimeError(f"Unexpected model output type: {type(output)}")

        # Logits shape: (1, 2, 224, 224)
        # Compute softmax probabilities across the 2 classes (0: Background, 1: Landslide)
        probs = torch.softmax(logits, dim=1)
        landslide_prob_tensor = probs[0, 1, :, :].cpu().numpy()

        # Generate binary prediction using threshold
        predicted_mask_224 = (landslide_prob_tensor >= threshold).astype(np.uint8)

    inference_duration = time.perf_counter() - start_time

    # Interpolate mask and probabilities back to original satellite raster dimensions
    orig_h, orig_w = preprocessed.original_shape
    if (orig_h, orig_w) == (224, 224):
        mask_orig = predicted_mask_224.copy()
        prob_orig = landslide_prob_tensor.copy()
    else:
        # Nearest neighbor for categorical mask to preserve discrete 0 and 1 values
        mask_orig = cv2.resize(predicted_mask_224, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        # Bilinear interpolation for continuous probability map
        prob_orig = cv2.resize(landslide_prob_tensor, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    return InferenceResult(
        mask_224=predicted_mask_224,
        mask_orig=mask_orig,
        landslide_prob_224=landslide_prob_tensor,
        landslide_prob_orig=prob_orig,
        inference_time_seconds=inference_duration
    )
