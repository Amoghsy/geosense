import os
import math
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import rasterio
from rasterio.features import shapes as rasterio_shapes
from shapely.geometry import shape, box, Point, mapping
from shapely.ops import transform as shapely_transform
from pyproj import CRS, Transformer


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate WGS84 geographic coordinates."""
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Invalid coordinates: lat={latitude}, lon={longitude}")
    if math.isnan(latitude) or math.isnan(longitude):
        raise ValueError("Coordinates cannot be NaN.")


def parse_bbox(bbox_str: str) -> Tuple[float, float, float, float]:
    """Parse 'min_lon,min_lat,max_lon,max_lat' into validated float tuple."""
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must have 4 comma-separated values: min_lon,min_lat,max_lon,max_lat")
    min_lon, min_lat, max_lon, max_lat = parts
    validate_coordinates(min_lat, min_lon)
    validate_coordinates(max_lat, max_lon)
    if min_lon > max_lon or min_lat > max_lat:
        raise ValueError("Invalid bbox: min coordinates must be <= max coordinates.")
    return min_lon, min_lat, max_lon, max_lat


def transform_geometry_to_wgs84(geom: Any, source_crs: str) -> Any:
    """Reproject a Shapely geometry from source_crs to EPSG:4326."""
    src = CRS.from_user_input(source_crs)
    dst = CRS.from_epsg(4326)
    if src == dst:
        return geom
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    return shapely_transform(transformer.transform, geom)


def transform_bounds_to_wgs84(
    bounds: Dict[str, float],
    source_crs: str,
) -> Dict[str, float]:
    """Reproject a bounds dict {left, bottom, right, top} to EPSG:4326."""
    b_geom = box(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])
    reproj = transform_geometry_to_wgs84(b_geom, source_crs)
    minx, miny, maxx, maxy = reproj.bounds
    return {
        "left": round(minx, 6),
        "bottom": round(miny, 6),
        "right": round(maxx, 6),
        "top": round(maxy, 6),
    }


def mask_to_geojson_polygons(
    georef_tif_path: str,
    max_polygons: int = 200,
) -> List[Dict[str, Any]]:
    """
    Convert a Phase 1 georeferenced binary segmentation mask GeoTIFF
    into EPSG:4326 GeoJSON Polygon features using rasterio.features.shapes.
    Returns [] if file is missing or lacks valid CRS/transform.
    """
    if not georef_tif_path or not os.path.isfile(georef_tif_path):
        return []

    features: List[Dict[str, Any]] = []
    with rasterio.open(georef_tif_path) as src:
        if src.crs is None or src.transform is None:
            return []
        mask = src.read(1)
        src_crs = str(src.crs)
        # Extract polygons where pixel value > 0 (landslide class)
        for geom_dict, val in rasterio_shapes(mask.astype(np.uint8), mask=(mask > 0), transform=src.transform):
            if val <= 0:
                continue
            geom = shape(geom_dict)
            if not geom.is_valid or geom.is_empty:
                continue
            geom_wgs84 = transform_geometry_to_wgs84(geom, src_crs)
            features.append(
                {
                    "type": "Feature",
                    "geometry": mapping(geom_wgs84),
                    "properties": {"pixel_class": int(val), "source_crs": src_crs},
                }
            )
            if len(features) >= max_polygons:
                break

    return features


def geometry_intersects_bbox(geom_dict: Dict[str, Any], bbox_tuple: Tuple[float, float, float, float]) -> bool:
    """Check spatial intersection between a GeoJSON geometry dict and (minx, miny, maxx, maxy)."""
    geom = shape(geom_dict)
    bbox_poly = box(*bbox_tuple)
    return bool(geom.intersects(bbox_poly))
