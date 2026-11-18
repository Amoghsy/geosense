# GeoSense Phase 1 — Satellite-Based Landslide Detection Backend

AI-powered satellite imagery landslide segmentation backend for GeoSense, utilizing the **IBM/NASA Prithvi Geospatial Foundation Model** (Prithvi-EO-2.0-300M) fine-tuned for pixel-level landslide detection ([`srivassid/prithvi-landslide`](https://huggingface.co/srivassid/prithvi-landslide)).

---

## 1. System Overview & Model Architecture

- **Model Repository:** `srivassid/prithvi-landslide`
- **Base Architecture:** `Prithvi-EO-2.0-300M-TL` (IBM/NASA Geospatial Foundation Model)
- **Framework:** `TerraTorch` / `PyTorch Lightning`
- **Task:** Binary Semantic Segmentation (`SemanticSegmentationTask`)
- **Factory:** `EncoderDecoderFactory`
- **Encoder:** Prithvi 3D Vision Transformer (`PrithviViT` with patch size `(1, 16, 16)`, embed dimension 1024, 24 transformer blocks)
- **Decoder:** `UperNetDecoder` with Pyramid Pooling Module (PPM) and Feature Pyramid Network (FPN)
- **Output Classes:** 2 (0: Non-Landslide / Background, 1: Landslide)
- **Fine-Tuning Benchmark:** Landslide4Sense multispectral benchmark

---

## 2. Supported Satellite Image Formats & Band Ordering

The Prithvi Landslide model operates on multispectral Earth observation data. **Standard 3-band consumer photographs (JPEG, PNG, smartphone cameras) are strictly rejected.**

### Supported Input Containers:
1. **Multi-band GeoTIFF (`.tif`, `.tiff`)**: Multi-band rasters with geospatial metadata (CRS and affine transforms).
2. **HDF5 (`.h5`, `.hdf5`)**: Standard Landslide4Sense format containing dataset key `img`.

### Required Satellite Bands (in exact sequence):
| Band Index | Band Name | Sentinel-2 Equivalent | Description |
|:---:|:---:|:---:|:---|
| 0 | `BLUE` | Band 2 (~490 nm) | Visible Blue |
| 1 | `GREEN` | Band 3 (~560 nm) | Visible Green |
| 2 | `RED` | Band 4 (~665 nm) | Visible Red |
| 3 | `NIR_BROAD` | Band 8 (~842 nm) | Broad Near-Infrared |
| 4 | `SWIR_1` | Band 11 (~1610 nm) | Short-Wave Infrared 1 |
| 5 | `SWIR_2` | Band 12 (~2190 nm) | Short-Wave Infrared 2 |

*Note:* If a 14-band Landslide4Sense container is provided, channels `[1, 2, 3, 7, 10, 11]` are automatically extracted.

### Normalization Statistics:
Channel-wise z-score normalization `(x - mean) / std` is applied using the exact benchmark parameters:
- `BLUE`: mean = -0.3074, std = 0.8775
- `GREEN`: mean = -0.1277, std = 0.8860
- `RED`: mean = -0.0625, std = 0.8869
- `NIR_BROAD`: mean = 0.0802, std = 0.8491
- `SWIR_1`: mean = 0.0823, std = 0.8848
- `SWIR_2`: mean = 0.0516, std = 0.9232

---

## 3. Project Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup and lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   └── satellite_routes.py     # Endpoints for health, status, detection, retrieval
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── model_loader.py         # Hugging Face checkpoint loading and caching
│   │   ├── preprocessing.py        # Band validation, resizing, normalization
│   │   ├── inference.py            # Forward pass through Prithvi ViT and UperNet
│   │   └── postprocessing.py       # Binary masks, RGB previews, colored overlay
│   ├── services/
│   │   ├── __init__.py
│   │   └── satellite_service.py    # Detection orchestration and artifact persistence
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── satellite_schema.py     # Pydantic request and response models
│   └── utils/
│       ├── __init__.py
│       └── image_utils.py          # Visual stretches, overlays, GeoTIFF serialization
├── uploads/                        # Uploaded satellite files
├── results/                        # Generated masks, overlays, GeoTIFFs, metadata
├── model_weights/                  # Cached Prithvi model weights (last.ckpt)
├── tests/                          # Automated test suite and sample GeoTIFF fixtures
│   ├── __init__.py
│   ├── sample_satellite_6band.tif  # Genuine Landslide4Sense test raster
│   └── test_api.py
├── requirements.txt                # Python package dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
└── README.md                       # Comprehensive guide
```

---

## 4. Setup and Installation (Windows PowerShell)

### Prerequisites:
- Python 3.11 or 3.12 (64-bit)
- PowerShell 5.1+ or PowerShell Core

### Step 1: Clone or Navigate to the Backend Folder
```powershell
cd d:\mywork\PBL\geosense\backend
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If script execution is disabled on your system, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 4: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Model Download & Weights Setup

The model checkpoint `last.ckpt` (~3.78 GB) is hosted on Hugging Face at `srivassid/prithvi-landslide`.

### Automatic Download:
The backend automatically downloads and caches `last.ckpt` into `backend/model_weights/` on startup or on the first detection request.

### Manual Download (Optional):
You can pre-download the checkpoint using `huggingface_hub`:
```powershell
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('srivassid/prithvi-landslide', 'last.ckpt', local_dir='model_weights')"
```

---

## 6. Running the FastAPI Server

Start the server using `uvicorn`:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at:
- **Base URL:** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 7. API Endpoints Reference

### 1. Health Check
- **Method:** `GET`
- **URL:** `/api/health`
- **Response:**
```json
{
  "status": "healthy",
  "service": "GeoSense Satellite Detection API"
}
```

### 2. Model Status
- **Method:** `GET`
- **URL:** `/api/model/status`
- **Response:**
```json
{
  "model_repository": "srivassid/prithvi-landslide",
  "status": "ready",
  "device": "cpu",
  "model_version": "main",
  "checkpoint_path": "D:\\mywork\\PBL\\geosense\\backend\\model_weights\\last.ckpt",
  "supported_input_formats": ["GeoTIFF (.tif, .tiff)", "HDF5 (.h5)"],
  "required_bands": ["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"],
  "expected_dimensions": "224x224 (multispectral bands resized/resampled for Prithvi ViT)",
  "error_details": null
}
```

### 3. Landslide Detection
- **Method:** `POST`
- **URL:** `/api/satellite/detect`
- **Content-Type:** `multipart/form-data`
- **Field:** `file` (Upload a 6-band or 14-band GeoTIFF or HDF5)
- **Response:**
```json
{
  "success": true,
  "result_id": "a1b2c3d4e5f6",
  "model": "srivassid/prithvi-landslide",
  "detection": {
    "landslide_detected": true,
    "landslide_pixel_percentage": 4.82,
    "total_pixels": 16384,
    "landslide_pixels": 790
  },
  "geospatial": {
    "has_georeference": true,
    "crs": "EPSG:4326",
    "bounds": {
      "left": 76.5,
      "bottom": 31.0,
      "right": 76.6,
      "top": 31.1
    },
    "affine_transform": [0.00078125, 0.0, 76.5, 0.0, -0.00078125, 31.1]
  },
  "files": {
    "original_image": "/api/satellite/results/a1b2c3d4e5f6/original",
    "segmentation_mask": "/api/satellite/results/a1b2c3d4e5f6/mask",
    "overlay": "/api/satellite/results/a1b2c3d4e5f6/overlay",
    "georeferenced_mask_tif": "/api/satellite/results/a1b2c3d4e5f6/geotiff"
  },
  "processing_time_seconds": 1.842
}
```

### 4. Retrieve Analysis Metadata
- **Method:** `GET`
- **URL:** `/api/satellite/results/{result_id}`

### 5. Retrieve Overlay Image
- **Method:** `GET`
- **URL:** `/api/satellite/results/{result_id}/overlay`
- **Content-Type:** `image/png`

### 6. Download Georeferenced GeoTIFF Mask
- **Method:** `GET`
- **URL:** `/api/satellite/results/{result_id}/geotiff`
- **Content-Type:** `image/tiff`

---

## 8. Testing with Swagger UI

1. Open your browser and navigate to:
   ```
   http://localhost:8000/docs
   ```
2. Locate `POST /api/satellite/detect`.
3. Click **"Try it out"**.
4. In the `file` parameter, upload `backend/tests/sample_satellite_6band.tif`.
5. Click **"Execute"**.
6. View the structured JSON detection response with landslide percentage, pixel counts, and file links.
7. Open the returned `/api/satellite/results/{result_id}/overlay` URL to view the visualized landslide detection mask overlay!

---

## 9. Running the Automated Test Suite

Run pytest in PowerShell:
```powershell
pytest -v tests/test_api.py
```

The test suite validates:
- API health and model status endpoints
- Rejection of non-satellite text files
- Rejection of consumer mobile JPEG photographs
- Rejection of standard 3-band RGB imagery
- Rejection of incorrect band counts
- Multispectral preprocessing and normalization
- Mask and overlay visual rendering
- Full inference and result retrieval

---

## 10. Common Errors and Troubleshooting

| Error | Cause | Resolution |
|:---|:---|:---|
| `Standard 3-band RGB photograph detected` | Uploaded a standard 3-channel RGB image. | The Prithvi model strictly requires 6 satellite bands (`B2, B3, B4, B8, B11, B12`). Upload a multispectral GeoTIFF. |
| `Unsupported number of bands: X` | Uploaded a GeoTIFF with band count not equal to 6 or 14. | Provide a 6-band Sentinel-2 tile or 14-band Landslide4Sense raster. |
| `Prithvi Model Unavailable` | Checkpoint is currently downloading or cannot be accessed. | Check `/api/model/status` to monitor download progress or verify network access to Hugging Face. |
| `CUDA out of memory` | GPU memory exhausted during inference. | Set `DEVICE=cpu` in `.env` to execute inference on host CPU. |
| `RasterioIOError` | Uploaded file is corrupted or not a valid raster. | Ensure the file was completely uploaded and is a valid GeoTIFF format. |
