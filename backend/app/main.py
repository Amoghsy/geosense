import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.satellite_routes import router as satellite_router
from app.ml.model_loader import get_model_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("geosense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    Checks hardware acceleration and initializes model manager on startup.
    """
    logger.info("Initializing GeoSense Satellite Landslide Detection Backend...")
    manager = get_model_manager()
    logger.info(f"Target compute device: {manager.device}")
    logger.info(f"Configured Prithvi model repository: {manager.repo_id}")

    # Note: Model loading is lazy or can be warmed up in the background
    yield
    logger.info("Shutting down GeoSense Backend.")


app = FastAPI(
    title="GeoSense — Satellite-Based Landslide Detection API",
    description="""
# GeoSense Phase 1 Backend

AI-powered landslide segmentation API utilizing the **IBM/NASA Prithvi Geospatial Foundation Model (Prithvi-EO-2.0-300M)** fine-tuned for landslide detection (`srivassid/prithvi-landslide`).

### Capabilities:
- **Multispectral Satellite Ingestion**: Supports multi-band GeoTIFF and HDF5 inputs with 6 optical bands (`BLUE`, `GREEN`, `RED`, `NIR_BROAD`, `SWIR_1`, `SWIR_2`).
- **Deep Segmentation**: Generates pixel-accurate landslide hazard masks using Prithvi ViT and U-Net / UPerNet decoders.
- **GIS Integration**: Preserves Coordinate Reference System (CRS) and affine georeferencing metadata, outputting georeferenced raster masks.
- **Visual Analytics**: Produces true-color satellite previews and highlighted overlays.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(satellite_router, prefix="/api")

# Static files for results directory
results_dir = os.path.abspath(
    os.getenv("RESULT_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"))
)
os.makedirs(results_dir, exist_ok=True)
app.mount("/results", StaticFiles(directory=results_dir), name="results")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "GeoSense Satellite Landslide Detection API",
        "documentation": "/docs",
        "health": "/api/health",
        "model_status": "/api/model/status"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
