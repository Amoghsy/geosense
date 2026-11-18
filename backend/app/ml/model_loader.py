import os
import logging
from typing import Optional, Dict, Any
import torch
import yaml
from huggingface_hub import hf_hub_download

from terratorch.tasks import SemanticSegmentationTask

logger = logging.getLogger("geosense.model_loader")

# Default model configuration
DEFAULT_REPO_ID = os.getenv("MODEL_REPO_ID", "srivassid/prithvi-landslide")
DEFAULT_REVISION = os.getenv("MODEL_REVISION", "main")
DEFAULT_CHECKPOINT_NAME = os.getenv("MODEL_CHECKPOINT_FILE", "last.ckpt")
DEFAULT_CONFIG_NAME = os.getenv("MODEL_CONFIG_FILE", "config.yaml")
DEFAULT_MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model_weights"))

# Fallback architecture configuration matching srivassid/prithvi-landslide config.yaml
DEFAULT_ARCHITECTURE_CONFIG = {
    "model_factory": "EncoderDecoderFactory",
    "model_args": {
        "backbone": "prithvi_eo_v2_300",
        "backbone_pretrained": False,
        "decoder": "UperNetDecoder",
        "num_classes": 2,
        "rescale": True,
        "backbone_bands": [
            "BLUE",
            "GREEN",
            "RED",
            "NIR_BROAD",
            "SWIR_1",
            "SWIR_2"
        ],
        "head_dropout": 0.1,
        "decoder_channels": 256,
        "head_channel_list": [128, 64],
        "necks": [
            {"name": "SelectIndices", "indices": [5, 11, 17, 23]},
            {"name": "ReshapeTokensToImage"}
        ]
    }
}


class ModelLoadingError(Exception):
    """Raised when model loading fails."""
    pass


class PrithviModelManager:
    _instance: Optional["PrithviModelManager"] = None

    def __init__(self):
        self.repo_id = DEFAULT_REPO_ID
        self.revision = DEFAULT_REVISION
        self.checkpoint_filename = DEFAULT_CHECKPOINT_NAME
        self.config_filename = DEFAULT_CONFIG_NAME
        self.model_dir = os.path.abspath(DEFAULT_MODEL_DIR)
        os.makedirs(self.model_dir, exist_ok=True)

        # Detect compute device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[SemanticSegmentationTask] = None
        self.status: str = "not_loaded"
        self.error_details: Optional[str] = None
        self.checkpoint_path: Optional[str] = None
        self.config_path: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "PrithviModelManager":
        if cls._instance is None:
            cls._instance = PrithviModelManager()
        return cls._instance

    def get_status_info(self) -> Dict[str, Any]:
        """Return structured status metadata for the API."""
        return {
            "model_repository": self.repo_id,
            "status": self.status,
            "device": str(self.device),
            "model_version": self.revision,
            "checkpoint_path": self.checkpoint_path,
            "supported_input_formats": ["GeoTIFF (.tif, .tiff)", "HDF5 (.h5)"],
            "required_bands": ["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"],
            "expected_dimensions": "224x224 (multispectral bands resized/resampled for Prithvi ViT)",
            "error_details": self.error_details
        }

    def _resolve_config_path(self) -> str:
        """Download or locate config.yaml."""
        local_cfg = os.path.join(self.model_dir, self.config_filename)
        if os.path.isfile(local_cfg):
            return local_cfg

        logger.info(f"Downloading {self.config_filename} from {self.repo_id}...")
        try:
            downloaded = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.config_filename,
                revision=self.revision,
                local_dir=self.model_dir
            )
            return downloaded
        except Exception as e:
            logger.warning(f"Could not download config from HF Hub: {e}. Using bundled config.")
            return ""

    def _resolve_checkpoint_path(self) -> Optional[str]:
        """Locate local checkpoint or download from Hugging Face Hub."""
        # 1. Direct file in model_dir
        local_direct = os.path.join(self.model_dir, self.checkpoint_filename)
        if os.path.isfile(local_direct) and os.path.getsize(local_direct) > 1024 * 1024 * 100:  # > 100MB
            return local_direct

        # 2. Check for snapshots in cache
        for root, _, files in os.walk(self.model_dir):
            if self.checkpoint_filename in files:
                p = os.path.join(root, self.checkpoint_filename)
                if os.path.isfile(p) and os.path.getsize(p) > 1024 * 1024 * 100:
                    return p

        # 3. Download from HF Hub
        logger.info(f"Downloading checkpoint {self.checkpoint_filename} from {self.repo_id}...")
        self.status = "downloading"
        try:
            downloaded = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.checkpoint_filename,
                revision=self.revision,
                local_dir=self.model_dir
            )
            return downloaded
        except Exception as e:
            self.status = "failed"
            self.error_details = f"Failed to download checkpoint from Hugging Face Hub ({self.repo_id}): {str(e)}"
            logger.error(self.error_details)
            return None

    def load_model(self, force_reload: bool = False) -> SemanticSegmentationTask:
        """
        Load the Prithvi Landslide model onto the selected device once and cache in memory.
        """
        if self.model is not None and not force_reload:
            return self.model

        self.status = "loading"
        self.error_details = None

        try:
            # 1. Resolve configuration
            config_file = self._resolve_config_path()
            model_factory = DEFAULT_ARCHITECTURE_CONFIG["model_factory"]
            model_args = DEFAULT_ARCHITECTURE_CONFIG["model_args"]

            if config_file and os.path.isfile(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        cfg_data = yaml.safe_load(f)
                    if "model" in cfg_data and "init_args" in cfg_data["model"]:
                        init_args = cfg_data["model"]["init_args"]
                        if "model_factory" in init_args:
                            model_factory = init_args["model_factory"]
                        if "model_args" in init_args:
                            model_args = init_args["model_args"]
                            # Backbone weights are loaded via checkpoint
                            model_args["backbone_pretrained"] = False
                    self.config_path = config_file
                except Exception as e:
                    logger.warning(f"Error parsing config.yaml ({e}), using default architecture parameters.")

            # 2. Locate checkpoint
            ckpt_path = self._resolve_checkpoint_path()
            if not ckpt_path or not os.path.isfile(ckpt_path):
                msg = (
                    f"Model checkpoint '{self.checkpoint_filename}' is not available. "
                    f"Current status: {self.status}. Details: {self.error_details or 'Checkpoint file missing'}"
                )
                self.status = "failed" if self.status != "downloading" else "downloading"
                self.error_details = msg
                raise ModelLoadingError(msg)

            self.checkpoint_path = ckpt_path
            logger.info(f"Loading checkpoint from: {ckpt_path} on {self.device}...")

            # 3. Instantiate model architecture
            task = SemanticSegmentationTask(
                model_args=model_args,
                model_factory=model_factory
            )

            # 4. Load weights from checkpoint
            # Read checkpoint state dictionary safely
            checkpoint_data = torch.load(ckpt_path, map_location="cpu", weights_only=False)
            if isinstance(checkpoint_data, dict) and "state_dict" in checkpoint_data:
                state_dict = checkpoint_data["state_dict"]
            elif isinstance(checkpoint_data, dict):
                state_dict = checkpoint_data
            else:
                raise ModelLoadingError("Loaded checkpoint does not contain a state dictionary.")

            # Clean state dict keys if needed
            clean_state_dict = {}
            for k, v in state_dict.items():
                # LightningModule might prefix keys with 'model.' or similar
                clean_state_dict[k] = v

            missing, unexpected = task.load_state_dict(clean_state_dict, strict=False)
            if missing:
                logger.info(f"State dict missing keys count: {len(missing)}")
            if unexpected:
                logger.info(f"State dict unexpected keys count: {len(unexpected)}")

            task.to(self.device)
            task.eval()

            self.model = task
            self.status = "ready"
            self.error_details = None
            logger.info(f"Prithvi Landslide model successfully loaded on {self.device}.")
            return self.model

        except Exception as e:
            if self.status != "downloading":
                self.status = "failed"
            self.error_details = f"Failed to load Prithvi model: {str(e)}"
            logger.error(self.error_details, exc_info=True)
            raise ModelLoadingError(self.error_details)


# Module-level access functions
def get_model_manager() -> PrithviModelManager:
    return PrithviModelManager.get_instance()


def get_loaded_model() -> SemanticSegmentationTask:
    manager = get_model_manager()
    return manager.load_model()
