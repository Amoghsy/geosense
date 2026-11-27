import time
from dataclasses import dataclass, field
from typing import List, Dict, Any

import numpy as np
import torch
import cv2

from app.ml.susceptibility_model_loader import (
    get_susceptibility_model_manager,
    DECISION_THRESHOLD,
)
from app.ml.susceptibility_preprocessing import PreprocessedSusceptibilityData

PATCH_SIZE = 224


@dataclass
class SusceptibilityInferenceResult:
    raw_logit: float
    susceptibility_score: float
    decision_threshold: float
    is_susceptible: bool
    susceptibility_class: str
    tile_count: int
    tile_scores: List[Dict[str, Any]] = field(default_factory=list)
    inference_time_seconds: float = 0.0


def _resize_chw(arr_chw: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    resized = np.zeros((arr_chw.shape[0], target_h, target_w), dtype=np.float32)
    for c in range(arr_chw.shape[0]):
        resized[c] = cv2.resize(arr_chw[c], (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    return resized


def run_susceptibility_inference(
    preprocessed: PreprocessedSusceptibilityData,
) -> SusceptibilityInferenceResult:
    """
    Execute real inference on MultimodalLandslideModel:
    - Single-patch inference if dimensions <= 224x224 (resampling to 224x224 if smaller).
    - Non-overlapping 224x224 patch tiling if dimensions > 224x224, preserving tile coordinates.
    """
    manager = get_susceptibility_model_manager()
    model = manager.get_model()
    device = manager.device

    h, w = preprocessed.original_shape
    rgb_chw = preprocessed.rgb_tensor_chw
    terrain_chw = preprocessed.terrain_tensor_chw

    start_time = time.perf_counter()
    tile_scores: List[Dict[str, Any]] = []

    with torch.inference_mode():
        if h <= PATCH_SIZE and w <= PATCH_SIZE:
            if h != PATCH_SIZE or w != PATCH_SIZE:
                rgb_patch = _resize_chw(rgb_chw, PATCH_SIZE, PATCH_SIZE)
                terrain_patch = _resize_chw(terrain_chw, PATCH_SIZE, PATCH_SIZE)
            else:
                rgb_patch = rgb_chw
                terrain_patch = terrain_chw

            rgb_t = torch.from_numpy(rgb_patch).unsqueeze(0).to(device)
            terrain_t = torch.from_numpy(terrain_patch).unsqueeze(0).to(device)
            logit = float(model(rgb_t, terrain_t).squeeze().cpu().item())
            score = float(torch.sigmoid(torch.tensor(logit)).item())

            tile_scores.append(
                {
                    "row": 0,
                    "col": 0,
                    "y_start": 0,
                    "y_end": h,
                    "x_start": 0,
                    "x_end": w,
                    "raw_logit": round(logit, 6),
                    "susceptibility_score": round(score, 6),
                    "is_susceptible": score >= DECISION_THRESHOLD,
                }
            )
            agg_logit = logit
            agg_score = score
        else:
            # Tiled evaluation across 224x224 patches
            y_starts = list(range(0, h, PATCH_SIZE))
            x_starts = list(range(0, w, PATCH_SIZE))
            logits_list: List[float] = []
            scores_list: List[float] = []

            for r_idx, y0 in enumerate(y_starts):
                for c_idx, x0 in enumerate(x_starts):
                    y1 = min(y0 + PATCH_SIZE, h)
                    x1 = min(x0 + PATCH_SIZE, w)

                    rgb_sub = rgb_chw[:, y0:y1, x0:x1]
                    terrain_sub = terrain_chw[:, y0:y1, x0:x1]

                    if rgb_sub.shape[1] != PATCH_SIZE or rgb_sub.shape[2] != PATCH_SIZE:
                        rgb_sub = _resize_chw(rgb_sub, PATCH_SIZE, PATCH_SIZE)
                        terrain_sub = _resize_chw(terrain_sub, PATCH_SIZE, PATCH_SIZE)

                    rgb_t = torch.from_numpy(rgb_sub).unsqueeze(0).to(device)
                    terrain_t = torch.from_numpy(terrain_sub).unsqueeze(0).to(device)
                    logit = float(model(rgb_t, terrain_t).squeeze().cpu().item())
                    score = float(torch.sigmoid(torch.tensor(logit)).item())

                    logits_list.append(logit)
                    scores_list.append(score)
                    tile_scores.append(
                        {
                            "row": r_idx,
                            "col": c_idx,
                            "y_start": y0,
                            "y_end": y1,
                            "x_start": x0,
                            "x_end": x1,
                            "raw_logit": round(logit, 6),
                            "susceptibility_score": round(score, 6),
                            "is_susceptible": score >= DECISION_THRESHOLD,
                        }
                    )

            agg_logit = float(np.mean(logits_list))
            agg_score = float(np.max(scores_list))

    elapsed = time.perf_counter() - start_time
    is_susceptible = agg_score >= DECISION_THRESHOLD
    susceptibility_class = "Susceptible" if is_susceptible else "Non-Susceptible"

    return SusceptibilityInferenceResult(
        raw_logit=round(agg_logit, 6),
        susceptibility_score=round(agg_score, 6),
        decision_threshold=DECISION_THRESHOLD,
        is_susceptible=is_susceptible,
        susceptibility_class=susceptibility_class,
        tile_count=len(tile_scores),
        tile_scores=tile_scores,
        inference_time_seconds=round(elapsed, 4),
    )
