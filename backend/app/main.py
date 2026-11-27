import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.api.satellite_routes import router as satellite_router
from app.api.susceptibility_routes import router as susceptibility_router
from app.ml.model_loader import get_model_manager
from app.db.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("geosense")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
RESULTS_DIR = os.path.abspath(
    os.getenv("RESULT_DIR", os.path.join(BASE_DIR, "results"))
)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    Checks hardware acceleration and initializes model manager on startup.
    """
    logger.info("Initializing GeoSense Satellite Landslide Detection Backend...")
    init_db()
    manager = get_model_manager()
    logger.info(f"Target compute device: {manager.device}")
    logger.info(f"Configured Prithvi model repository: {manager.repo_id}")
    yield
    logger.info("Shutting down GeoSense Backend.")


app = FastAPI(
    title="GeoSense — Satellite-Based Landslide Detection API",
    description="""
# GeoSense Phase 1 Backend

AI-powered landslide detection API utilizing the **IBM/NASA Prithvi Geospatial Foundation Model (Prithvi-EO-2.0-300M)** fine-tuned for landslide detection (`srivassid/prithvi-landslide`).

### Capabilities:
- **Multispectral Satellite Ingestion**: Supports multi-band GeoTIFF and HDF5 inputs with 6 optical bands (`BLUE`, `GREEN`, `RED`, `NIR_BROAD`, `SWIR_1`, `SWIR_2`).
- **Deep Segmentation**: Generates pixel-accurate landslide hazard masks using Prithvi ViT and UPerNet decoders.
- **Tiled Sliding-Window Inference**: Seamless Hann-window blending for large-scale high-resolution satellite scenes.
- **GIS Integration**: Preserves Coordinate Reference System (CRS) and affine georeferencing metadata, outputting georeferenced raster masks.
- **Visual Analytics**: Produces true-color satellite previews, binary masks, and highlighted overlays.
- **Testing Interface**: Built-in web dashboard at `/` and `/ui`.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend / mobile / desktop integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints at both root and /api prefixes for flexibility and backward compatibility
app.include_router(satellite_router)
app.include_router(satellite_router, prefix="/api")
app.include_router(susceptibility_router)
app.include_router(susceptibility_router, prefix="/api")

# Static files for results directory
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# Static files for UI assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    """Serve the interactive HTML testing web interface."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file, media_type="text/html")
    return HTMLResponse("<h1>GeoSense Phase 1 Backend</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui_alias():
    """Alias for UI dashboard."""
    return await serve_ui()


@app.get("/susceptibility-ui", response_class=HTMLResponse, include_in_schema=False)
async def serve_susceptibility_ui():
    """Serve the temporary HTML testing web interface for Phase 2 Susceptibility Analysis."""
    html_file = os.path.join(STATIC_DIR, "susceptibility.html")
    if os.path.isfile(html_file):
        return FileResponse(html_file, media_type="text/html")
    return HTMLResponse("<h1>GeoSense Phase 2 Susceptibility</h1><p>Visit <a href='/docs'>/docs</a></p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
