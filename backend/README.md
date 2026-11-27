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
- **Inference Modes:**
  - Standard single patch (resampled to 224×224 for individual patches).
  - Tiled sliding-window inference with 2D Hann window blending for large satellite scenes.

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
│   ├── main.py                     # FastAPI application setup, lifespan, and UI serving
│   ├── api/
│   │   ├── __init__.py
│   │   └── satellite_routes.py     # Endpoints for health, status, detection, retrieval
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── model_loader.py         # Hugging Face checkpoint loading and caching
│   │   ├── preprocessing.py        # Band validation, resizing, normalization, NoData masking
│   │   ├── inference.py            # Forward pass & tiled Hann-window inference
│   │   └── postprocessing.py       # Binary masks, RGB previews, colored overlay, GeoTIFF
│   ├── services/
│   │   ├── __init__.py
│   │   └── satellite_service.py    # Detection orchestration and structured artifact persistence
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── satellite_schema.py     # Pydantic request and response models
│   ├── static/
│   │   └── index.html              # Interactive HTML testing web dashboard
│   └── utils/
│       ├── __init__.py
│       └── image_utils.py          # Visual stretches, overlays, GeoTIFF serialization
├── uploads/                        # Uploaded satellite files
├── results/                        # Generated detection artifacts and per-detection folders
│   └── detections/
│       └── {detection_id}/
│           ├── original.png
│           ├── mask.png
│           ├── overlay.png
│           ├── georeferenced_mask.tif
│           └── result.json
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

### Step 1: Navigate to the Backend Folder
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

## 5. Model Weights Setup

The model checkpoint `last.ckpt` (~3.78 GB) is hosted on Hugging Face at `srivassid/prithvi-landslide`.

The backend automatically loads and caches `last.ckpt` into `backend/model_weights/`. It uses a singleton `ModelManager` initialized on startup, auto-detecting CUDA if a GPU is available or falling back to CPU.

---

## 6. Running the Backend & Web Testing Dashboard

Start the server using `uvicorn`:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server provides:
- **Interactive Testing Web UI:** `http://localhost:8000/` or `http://localhost:8000/ui`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 7. Interactive Web Testing Interface (`/` & `/ui`)

The backend includes a built-in dark-themed web dashboard for testing:
- **Live Model Status:** Shows real-time Prithvi ViT readiness and compute device (CPU/CUDA).
- **Drag-and-Drop Ingestion:** Supports `.tif`, `.tiff`, and `.h5` files.
- **Validation Alerts:** Immediate clear feedback on invalid formats or missing bands.
- **Visual Switcher:** Side-by-side or tabbed inspection of True-Color RGB satellite composite, Binary Segmentation Mask, and Colored Overlay.
- **Statistical Dashboard:** Displays Detection Status (DETECTED / CLEAR), Landslide Coverage %, Valid Pixels, Latency, CRS, and Dimensions.
- **Direct Downloads:** One-click download of binary mask PNG, overlay PNG, georeferenced GeoTIFF, and metadata JSON.

---

## 8. API Endpoints Reference

All endpoints are accessible directly and via the `/api` prefix for backward compatibility.

### 1. Health Check
- **Method:** `GET`
- **URL:** `/health` (or `/api/health`)
- **Response:**
```json
{
  "status": "healthy",
  "service": "GeoSense Satellite Detection API"
}
```

### 2. Model Status
- **Method:** `GET`
- **URL:** `/model/status` (or `/api/model/status`)
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
- **URL:** `/detect` (or `/api/satellite/detect`)
- **Content-Type:** `multipart/form-data`
- **Field:** `file` (Upload a 6-band or 14-band GeoTIFF or HDF5)
- **Response:**
```json
{
  "success": true,
  "result_id": "a1b2c3d4e5f6",
  "detection_id": "a1b2c3d4e5f6",
  "status": "completed",
  "model": "srivassid/prithvi-landslide",
  "model_version": "main",
  "timestamp": "2026-11-27T06:58:30.123456+00:00",
  "detection": {
    "landslide_detected": true,
    "landslide_pixel_percentage": 4.82,
    "detected_area_percentage": 4.82,
    "total_pixels": 16384,
    "total_valid_pixels": 16384,
    "nodata_pixels": 0,
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
    "affine_transform": [0.00078125, 0.0, 76.5, 0.0, -0.00078125, 31.1],
    "image_dimensions": {
      "width": 128,
      "height": 128
    }
  },
  "files": {
    "original_image": "/detect/a1b2c3d4e5f6/original",
    "segmentation_mask": "/detect/a1b2c3d4e5f6/mask",
    "overlay": "/detect/a1b2c3d4e5f6/overlay",
    "georeferenced_mask_tif": "/detect/a1b2c3d4e5f6/geotiff",
    "result_json": "/detect/a1b2c3d4e5f6"
  },
  "processing_time_seconds": 0.742
}
```

### 4. Retrieve Detection Result Metadata
- **Method:** `GET`
- **URL:** `/detect/{detection_id}` (or `/api/satellite/results/{result_id}`)

### 5. Retrieve Colored Overlay Image
- **Method:** `GET`
- **URL:** `/detect/{detection_id}/overlay` (or `/api/satellite/results/{result_id}/overlay`)
- **Content-Type:** `image/png`

### 6. Retrieve True-Color RGB Original Image
- **Method:** `GET`
- **URL:** `/detect/{detection_id}/original` (or `/api/satellite/results/{result_id}/original`)
- **Content-Type:** `image/png`

### 7. Retrieve Binary Segmentation Mask
- **Method:** `GET`
- **URL:** `/detect/{detection_id}/mask` (or `/api/satellite/results/{result_id}/mask`)
- **Content-Type:** `image/png`

### 8. Download Georeferenced GeoTIFF Mask
- **Method:** `GET`
- **URL:** `/detect/{detection_id}/geotiff` (or `/api/satellite/results/{result_id}/geotiff`)
- **Content-Type:** `image/tiff`

---

## 9. Running the Automated Test Suite

Run pytest in PowerShell:
```powershell
python -m pytest backend/tests/test_api.py -v
```

The test suite validates:
- Interactive HTML test UI serving at `/` and `/ui`
- API health and model status endpoints
- Rejection of non-satellite text files
- Rejection of consumer mobile JPEG photographs
- Rejection of standard 3-band RGB imagery
- Rejection of incorrect band counts
- Rejection of empty/all-NoData rasters
- Multispectral preprocessing and normalization
- Mask, overlay, and GeoTIFF visual rendering
- Full inference and structured artifact retrieval

---

## 10. Common Errors and Troubleshooting

| Error | Cause | Resolution |
|:---|:---|:---|
| `Standard 3-band RGB photograph detected` | Uploaded a standard 3-channel RGB image. | The Prithvi model strictly requires 6 satellite bands (`B2, B3, B4, B8, B11, B12`). Upload a multispectral GeoTIFF. |
| `Unsupported number of bands: X` | Uploaded a GeoTIFF with band count not equal to 6 or 14. | Provide a 6-band Sentinel-2 tile or 14-band Landslide4Sense raster. |
| `Satellite image contains no valid data` | Uploaded raster is entirely NoData or NaN values. | Provide satellite imagery with valid reflectance values. |
| `Prithvi Model Unavailable` | Checkpoint is currently loading or cannot be accessed. | Check `/model/status` to monitor loading status. |
| `CUDA out of memory` | GPU memory exhausted during inference. | Set `DEVICE=cpu` in `.env` to execute inference on host CPU. |
| `RasterioIOError` | Uploaded file is corrupted or not a valid raster. | Ensure the file was completely uploaded and is a valid GeoTIFF format. |


---

## 11. Phase 2 — Multimodal Landslide Susceptibility Analysis

Phase 2 integrates the pretrained **Multimodal Late-Fusion** model from [`vinukatashidu/landslide-detection-multimodal`](https://huggingface.co/vinukatashidu/landslide-detection-multimodal) (pinned revision `8e972570b1f896f6fdc14de4d436df496342d3f0`).

### Model Architecture & Actual Task:
- **Architecture:** Late-Fusion network (`MultimodalLandslideModel`):
  - **Visual Branch:** Pretrained `ResNet50` on `[B4 (Red), B3 (Green), B2 (Blue)]` (ImageNet normalized) -> `2048-d`
  - **Physical Branch:** Custom 4-layer `TerrainCNN` on `[B8 (NIR), DEM, Slope]` (`[0, 1]` normalized via `5000`, `3000m`, `90°`) -> `256-d`
  - **Fusion Head:** MLP (`2304 -> 512 -> 1`) + `torch.sigmoid`
- **Actual Task:** Pre-event landslide susceptibility / vulnerability binary classification (`Susceptible` if `score >= 0.291`, else `Non-Susceptible`).
- **Evaluation Metrics (from Model Card):** ROC-AUC `0.7371`, F1 `0.7100`, Recall `91%`, Specificity `46%` (optimal threshold `0.291`).

### Supported Phase 2 Inputs:
- **6-band GeoTIFF (`.tif`, `.tiff`)** or **6-channel NumPy (`.npy`)** with exact channel order: `[B4 (Red), B3 (Green), B2 (Blue), B8 (NIR), DEM, Slope]`.
- Standard 3-band RGB photos (JPEG/PNG) and 3-band GeoTIFFs are strictly rejected.

### Phase 2 Endpoints & Testing UI:
- **Temporary HTML Dashboard:** `http://localhost:8000/susceptibility-ui`
- `GET /susceptibility/health` — Module health & model load state
- `GET /susceptibility/model/status` — Device, checkpoint path, supported inputs
- `GET /susceptibility/model/info` — Architecture, metrics, geographic limitations
- `POST /susceptibility/analyze` — Run inference on 6-channel `.tif` or `.npy` (supports `region_id` for all 8 North Eastern India states)
- `GET /susceptibility/analyze/{analysis_id}` — Retrieve analysis JSON (persisted in SQLite `geosense.db`)
- `GET /susceptibility/analyze/{analysis_id}/map` — Retrieve GeoJSON FeatureCollection (if input had valid CRS/transform)
- `GET /susceptibility/analyze/{analysis_id}/metadata` — Retrieve full metadata JSON

### Geographic Coverage & Known Limitations:
- Supports region tagging for Meghalaya, Sikkim, Assam, Arunachal Pradesh, Manipur, Mizoram, Nagaland, and Tripura.
- **Uncalibrated Prototype:** The pretrained weights are an academic prototype not locally calibrated for North Eastern India and do not incorporate live rainfall or seismic triggers (reserved for Phase 3).


---

## 12. Phase 3 — Weather-Integrated Dynamic Landslide Risk Engine

Phase 3 fuses live Open-Meteo weather, 30-day historical rainfall, Antecedent Wetness Index (AWI) proxy, 72-hour rainfall forecasts, terrain attributes, and verified Phase 1 & Phase 2 outputs into a transparent, configurable **0–100 Heuristic Risk Index**.

> **Important Disclaimer:** The Phase 3 Risk Index is a provisional heuristic score requiring regional calibration for North Eastern India. It is **not** a calibrated landslide probability and **not** a guarantee or exact timing prediction of a landslide event.

### Open-Meteo Integration (`weather_service.py`):
- **Current & 7d Past + 3d Forecast:** `https://api.open-meteo.com/v1/forecast` (`precipitation, temperature_2m, relative_humidity_2m, wind_speed_10m, weather_code`).
- **Historical Archive (up to 32 days):** `https://archive-api.open-meteo.com/v1/archive` (`hourly=precipitation`).
- **Caching & Freshness:** 15-minute TTL cache (`WEATHER_CACHE_TTL_SECONDS=900`), stale observation detection (`> 3h`), and strict separation of observed vs forecast timestamps.

### Rainfall Intelligence Engine (`landslide_weather_analyzer.py`):
- **Rolling Observed Windows:** `1h`, `3h`, `6h`, `24h`, `72h`, `7d`, `15d`, `30d` (missing hours marked incomplete, never silently zeroed).
- **Forecast Windows:** `next_3h`, `next_6h`, `next_24h`, `next_72h`.
- **Antecedent Wetness Index (AWI) Proxy:** `AWI(t) = P(t) + k * AWI(t-1)` (`k=0.85` configurable via `AWI_DECAY_K`). Labeled explicitly as a rainfall-based wetness proxy, **not** measured soil moisture.

### Dynamic Risk Fusion (`landslide_risk_engine.py`):
- **Configurable Weights:** `observed_rainfall (0.30)`, `forecast_rainfall (0.20)`, `baseline_susceptibility (0.25)`, `terrain (0.15)`, `satellite_detection (0.10)`. Unavailable factors are excluded and remaining weights normalized to `1.0`.
- **Provisional Categories:** `0–24 LOW`, `25–49 MODERATE`, `50–74 HIGH`, `75–100 CRITICAL`, or `INSUFFICIENT_DATA` if weather inputs fail.

### Phase 3 Endpoints & Testing UI:
- **Temporary Risk Dashboard:** `http://localhost:8000/risk-ui`
- `GET /weather/current?latitude=...&longitude=...`
- `GET /weather/rainfall?latitude=...&longitude=...`
- `POST /risk/analyze`
- `GET /risk/hotspots`
- `GET /risk/{location_id}`
- `GET /risk/{assessment_id}/explain`
- `GET /risk/{assessment_id}/history`


---

## 13. Phase 4 — Unified GIS Backend & Interactive Mapping

Phase 4 unifies Phases 1–3 into a spatial GIS layer management system and an interactive Leaflet dashboard.

### GIS Architecture & Storage:
- **Spatial Processing (`app/gis/geo_utils.py`):** `pyproj` CRS reprojection to `EPSG:4326`, `shapely` bounding-box & point-in-polygon intersection, and `rasterio.features.shapes` mask-to-polygon extraction for Phase 1 GeoTIFFs.
- **Database & PostGIS (`app/db/database.py` & `app/db/postgis_schema.sql`):** Spatial tables (`gis_layers`, `gis_features` with bounding-box indexes, `incidents`, `emergency_resources`) in SQLite `geosense.db`, plus a ready-to-run PostgreSQL/PostGIS schema (`GIST` indexes, `SRID 4326`).
- **Authentic Geographic Boundaries (`app/data/ne_india_states.geojson`):** Simplified ADM1 state boundaries for all 8 North Eastern India states sourced from **geoBoundaries gbOpen IND ADM1** (License: CC BY 2.5 IN). District boundaries are explicitly marked unavailable rather than fabricated.
- **Map Tiles:** OpenStreetMap standard tiles (`© OpenStreetMap contributors`).

### Phase 4 GIS Endpoints & Dashboard:
- **Interactive GIS Dashboard:** `http://localhost:8000/gis-ui`
- `GET /gis/health` — GIS backend & spatial dataset status
- `GET /gis/layers` & `GET /gis/layers/{layer_id}` — Unified layer catalog (Phase 1–3, terrain, incidents, emergency resources)
- `GET /gis/layers/{layer_id}/features` — Paginated GeoJSON FeatureCollection with `bbox`, `region`, `risk_category`, `start_date`, `end_date` filters
- `GET /gis/regions/states` & `GET /gis/regions/districts`
- `GET /gis/hotspots` — Elevated (`HIGH` / `CRITICAL`) Phase 3 grid locations
- `GET /gis/location` — Spatial query returning state + nearest/intersecting Phase 1–3 data
- `GET /gis/summary` — Real counts from stored assessments and detections


---

## 14. Phase 5 — Explainable AI (XAI) & Risk Trend Analysis

Phase 5 makes every Phase 3 risk assessment transparent, auditable, and trackable over time without fabricating historical records or forcing black-box attributions onto rule-based weights.

### Key Capabilities:
- **Factor Attribution (`risk_explanation_service.py`):** Exposes each factor's raw input value, normalized score (`0–100`), configured weight, effective normalized weight, exact contribution points (`normalized_score × effective_weight`), source, timestamp, and freshness.
- **Readable Natural-Language Explanations:** Generated directly from stored assessment values, distinguishing factors that increased vs reduced risk vs unavailable factors, and persisted in `risk_explanations` (`geosense.db`).
- **Trend Analysis & Comparison:** Tracks historical risk scores, category transitions, and rainfall shifts from stored assessments, and compares any two assessments side-by-side.
- **Interactive XAI Dashboard (`http://localhost:8000/xai-ui`):** Chart.js factor contribution bar chart, historical risk & rainfall line charts, and assessment comparison panel, directly linked from the Phase 4 GIS map (`/gis-ui`).

### Phase 5 Endpoints:
- `GET /risk/{assessment_id}/explanation`
- `GET /risk/{assessment_id}/contributing-factors`
- `GET /risk/{location_id}/trends`
- `GET /risk/{location_id}/comparison?assessment_id_1=...&assessment_id_2=...`


---

## 15. Phase 6 — AI Decision-Support Agent

Phase 6 implements a grounded **GeoSense Orchestrator Agent** that queries real Phases 1–5 services via callable backend tools, enforces role-based access (`citizen`, `field_officer`, `authority`), and retains session conversation context.

### Architecture & Execution Modes:
- **Google ADK Integration (`app/agent/orchestrator.py`):** Configured with `google.adk.agents.Agent` and all 9 GeoSense backend tools (`app/agent/tools.py`) when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is provided.
- **Grounded Deterministic Tool-Router:** Automatically active when no external LLM key is configured, routing natural-language queries and follow-up questions directly to real GeoSense services with zero fabricated data.
- **Chat UI (`http://localhost:8000/agent-ui`):** Role selector, suggested questions, session memory, tool execution badges, and structured visual cards, linked directly from the Phase 4 GIS Map (`/gis-ui`).

### Phase 6 Endpoints:
- `GET /agent/health`
- `POST /agent/sessions` & `GET /agent/sessions/{session_id}`
- `POST /agent/chat`
- `POST /agent/situation-report` (restricted to `field_officer` and `authority` roles)


---

## 16. Phase 7 — Emergency Resource Management

Phase 7 adds a centralized, role-gated geospatial emergency resource management system integrated with the Phase 4 GIS map and Phase 6 AI Decision-Support Agent.

### Supported Resource Categories:
`HOSPITAL`, `HEALTH_CENTRE`, `AMBULANCE`, `SHELTER`, `RESCUE_TEAM`, `FIRE_STATION`, `POLICE_STATION`, `RELIEF_CENTRE`, `HEAVY_EQUIPMENT`.

### Verification Workflow & Safeguards:
- **Verification Status:** `PENDING`, `VERIFIED`, `REJECTED`.
- **Operational Status:** `OPERATIONAL`, `TEMPORARILY_UNAVAILABLE`, `CLOSED`, `UNKNOWN`.
- **Availability Status:** `AVAILABLE`, `LIMITED`, `FULL`, `UNAVAILABLE`, `UNKNOWN`.
- Newly registered or OpenStreetMap-imported facilities always start as `PENDING` / `UNKNOWN` and are hidden from citizens until verified by an Authority. Private contacts are redacted for citizens, and straight-line Haversine distances are explicitly distinguished from road travel time.

### Phase 7 Endpoints & Dashboard:
- **Resource Management Dashboard:** `http://localhost:8000/resources-ui`
- `POST /resources`, `GET /resources`, `GET /resources/{resource_id}`, `PATCH /resources/{resource_id}`
- `POST /resources/{resource_id}/verify`, `PATCH /resources/{resource_id}/availability`, `GET /resources/{resource_id}/history`
- `GET /resources/near`, `GET /resources/recommend`, `GET /resources/statistics`, `POST /resources/import-osm`
