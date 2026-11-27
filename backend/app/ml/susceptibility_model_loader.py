import os
import logging
import threading
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
from torchvision import models
from huggingface_hub import hf_hub_download

logger = logging.getLogger("geosense.susceptibility_model_loader")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_MODEL_DIR = os.path.join(BASE_DIR, "model_weights")

SUSCEPTIBILITY_REPO_ID = os.getenv("PHASE2_MODEL_REPO_ID", "vinukatashidu/landslide-detection-multimodal")
SUSCEPTIBILITY_REVISION = os.getenv("PHASE2_MODEL_REVISION", "8e972570b1f896f6fdc14de4d436df496342d3f0")
SUSCEPTIBILITY_CHECKPOINT = os.getenv("PHASE2_MODEL_CHECKPOINT", "multimodal_stage2.pth")
DECISION_THRESHOLD = 0.291


class SusceptibilityModelError(Exception):
    """Raised when the Phase 2 multimodal model fails to download or load."""
    pass


class TerrainCNN(nn.Module):
    """4-layer CNN for physical terrain & NIR features [B8, DEM, Slope]."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return x.view(x.size(0), -1)


class MultimodalLandslideModel(nn.Module):
    """
    Multimodal Late-Fusion Architecture from vinukatashidu/landslide-detection-multimodal:
    - Visual Branch: ResNet50 on [B4 (Red), B3 (Green), B2 (Blue)] -> 2048-d
    - Physical Branch: TerrainCNN on [B8 (NIR), DEM, Slope] -> 256-d
    - Fusion Head: MLP (2304 -> 512 -> 1) -> scalar susceptibility logit
    """

    def __init__(self):
        super().__init__()
        resnet = models.resnet50(weights=None)
        self.resnet = nn.Sequential(*list(resnet.children())[:-1])
        self.terrain_cnn = TerrainCNN()
        self.fusion_head = nn.Sequential(
            nn.Linear(2304, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 1),
        )

    def forward(self, rgb: torch.Tensor, terrain: torch.Tensor) -> torch.Tensor:
        f_rgb = self.resnet(rgb)
        f_rgb = f_rgb.view(f_rgb.size(0), -1)
        f_terrain = self.terrain_cnn(terrain)
        f_combined = torch.cat((f_rgb, f_terrain), dim=1)
        return self.fusion_head(f_combined)


class SusceptibilityModelManager:
    """Singleton manager for loading and caching the Phase 2 Multimodal Landslide model."""

    def __init__(self):
        self.repo_id = SUSCEPTIBILITY_REPO_ID
        self.revision = SUSCEPTIBILITY_REVISION
        self.checkpoint_filename = SUSCEPTIBILITY_CHECKPOINT
        self.model_dir = os.path.abspath(os.getenv("MODEL_DIR", DEFAULT_MODEL_DIR))
        os.makedirs(self.model_dir, exist_ok=True)

        device_pref = os.getenv("DEVICE", "auto").lower()
        if device_pref == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif device_pref == "cpu":
            self.device = torch.device("cpu")
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model: Optional[MultimodalLandslideModel] = None
        self._checkpoint_path: Optional[str] = None
        self._status: str = "not_loaded"
        self._error: Optional[str] = None
        self._lock = threading.Lock()

    def ensure_checkpoint(self) -> str:
        local_ckpt = os.path.join(self.model_dir, self.checkpoint_filename)
        if os.path.isfile(local_ckpt) and os.path.getsize(local_ckpt) > 10_000_000:
            self._checkpoint_path = local_ckpt
            return local_ckpt

        logger.info(
            f"Downloading Phase 2 checkpoint '{self.checkpoint_filename}' from "
            f"{self.repo_id}@{self.revision}..."
        )
        downloaded = hf_hub_download(
            repo_id=self.repo_id,
            filename=self.checkpoint_filename,
            revision=self.revision,
            local_dir=self.model_dir,
        )
        self._checkpoint_path = downloaded
        return downloaded

    def get_model(self) -> MultimodalLandslideModel:
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            try:
                ckpt_path = self.ensure_checkpoint()
                logger.info(f"Loading Phase 2 MultimodalLandslideModel onto {self.device}...")
                model = MultimodalLandslideModel()
                state_dict = torch.load(ckpt_path, map_location=self.device, weights_only=True)
                model.load_state_dict(state_dict)
                model.to(self.device)
                model.eval()
                self._model = model
                self._status = "ready"
                self._error = None
                logger.info("Phase 2 MultimodalLandslideModel loaded and ready.")
                return self._model
            except Exception as exc:
                self._status = "failed"
                self._error = str(exc)
                logger.error(f"Failed to load Phase 2 model: {exc}")
                raise SusceptibilityModelError(
                    f"Failed to load {self.repo_id}@{self.revision}: {exc}"
                ) from exc

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_status_info(self) -> Dict[str, Any]:
        ckpt_path = self._checkpoint_path or os.path.join(self.model_dir, self.checkpoint_filename)
        has_ckpt = os.path.isfile(ckpt_path)
        current_status = self._status
        if self._model is not None:
            current_status = "ready"
        elif current_status == "not_loaded" and has_ckpt:
            current_status = "ready"

        return {
            "model_repository": self.repo_id,
            "model_revision": self.revision,
            "status": current_status,
            "device": str(self.device),
            "checkpoint_path": ckpt_path if has_ckpt else None,
            "supported_inputs": ["GeoTIFF (.tif, .tiff)", "NumPy Array (.npy)"],
            "required_channels": [
                "B4 (Red)",
                "B3 (Green)",
                "B2 (Blue)",
                "B8 (NIR)",
                "DEM (Elevation 0-3000m or normalized [0,1])",
                "Slope (0-90 deg or normalized [0,1])",
            ],
            "expected_patch_size": "224x224 per patch (larger georeferenced GeoTIFFs are tiled)",
            "actual_task": "Pre-event landslide susceptibility / vulnerability binary classification (patch-level probability)",
            "error_details": self._error,
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_repository": self.repo_id,
            "model_revision": self.revision,
            "license": "MIT",
            "architecture": {
                "name": "MultimodalLandslideModel (Late-Fusion)",
                "visual_branch": "ResNet50 (ImageNet-normalized RGB: B4, B3, B2 -> 2048-d)",
                "physical_branch": "TerrainCNN (4-layer Conv2d + BatchNorm + MaxPool -> 256-d on B8, DEM, Slope)",
                "fusion_head": "MLP (2304 -> 512 -> 1) + Sigmoid",
            },
            "actual_task": (
                "Pre-event landslide susceptibility / vulnerability binary classification "
                "producing a scalar probability score in [0, 1] per 224x224 multimodal patch."
            ),
            "supported_input_formats": ["GeoTIFF (.tif, .tiff) with 6 bands", "NumPy (.npy) with shape (6, H, W)"],
            "required_channels": ["B4 (Red)", "B3 (Green)", "B2 (Blue)", "B8 (NIR)", "DEM", "Slope"],
            "preprocessing_requirements": {
                "rgb_branch": "Scaled to [0,1], then ImageNet normalized (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])",
                "terrain_branch": "Normalized to [0,1] (NIR: 0-5000, DEM: 0-3000m, Slope: 0-90 deg)",
                "patch_dimensions": "224x224",
            },
            "output_format": {
                "raw_output": "Scalar logit -> torch.sigmoid(logit) in [0.0, 1.0]",
                "documented_decision_threshold": DECISION_THRESHOLD,
                "classes": {"Susceptible": f"score >= {DECISION_THRESHOLD}", "Non-Susceptible": f"score < {DECISION_THRESHOLD}"},
            },
            "evaluation_metrics": {
                "roc_auc": 0.7371,
                "f1_score": 0.7100,
                "recall": 0.91,
                "specificity": 0.46,
                "split_method": "GroupShuffleSplit by landslide_id to prevent spatial leakage",
            },
            "geographic_coverage_and_limitations": {
                "training_coverage": "Academic prototype dataset; exact geographic bounds not published in model card.",
                "northeast_india_applicability": (
                    "Experimental / uncalibrated for North Eastern India (Meghalaya, Sikkim, Assam, "
                    "Arunachal Pradesh, Manipur, Mizoram, Nagaland, Tripura). Must not be used as a standalone "
                    "operational hazard map without local calibration."
                ),
                "missing_dynamic_factors": "Does not ingest live rainfall, soil moisture, pore-water pressure, or seismic triggers (reserved for Phase 3).",
            },
        }


_manager_instance: Optional[SusceptibilityModelManager] = None


def get_susceptibility_model_manager() -> SusceptibilityModelManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SusceptibilityModelManager()
    return _manager_instance
