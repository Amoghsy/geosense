import os
import time
import uuid
import logging
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, Optional, Tuple, List

import httpx

from app.db.database import save_weather_observation

logger = logging.getLogger("geosense.weather_service")

OPEN_METEO_FORECAST_URL = os.getenv("OPEN_METEO_FORECAST_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_ARCHIVE_URL = os.getenv("OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
WEATHER_CACHE_TTL_SECONDS = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "900"))  # 15 min
STALE_OBSERVATION_HOURS = float(os.getenv("WEATHER_STALE_HOURS", "3.0"))

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def make_location_id(latitude: float, longitude: float) -> str:
    """Consistent 0.001-deg (~110m) grid identifier for weather caching and storage."""
    return f"loc_{latitude:.3f}_{longitude:.3f}"


def _parse_utc_hour(ts_str: str) -> datetime:
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class WeatherService:
    """
    Reusable asynchronous Open-Meteo client with TTL caching,
    historical archive + recent forecast merging, and stale/missing-data detection.
    """

    def __init__(self):
        self._cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    async def fetch_weather_bundle(
        self,
        latitude: float,
        longitude: float,
        location_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch current weather, 7d past + 3d hourly forecast, and 30d historical archive
        from Open-Meteo. Strictly separates observed vs forecast timestamps.
        """
        loc_id = location_id or make_location_id(latitude, longitude)
        cache_key = (round(latitude, 3), round(longitude, 3))
        now_mono = time.monotonic()

        if use_cache and cache_key in self._cache:
            cached_at, cached_bundle = self._cache[cache_key]
            if (now_mono - cached_at) < WEATHER_CACHE_TTL_SECONDS:
                bundle_copy = dict(cached_bundle)
                bundle_copy["cached"] = True
                return bundle_copy

        now_utc = datetime.now(timezone.utc)
        warnings: List[str] = []
        sources: List[str] = []

        forecast_data: Optional[Dict[str, Any]] = None
        archive_data: Optional[Dict[str, Any]] = None

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Open-Meteo Forecast API (current + past 7 days + next 3 days)
            try:
                f_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "hourly": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m",
                    "past_days": 7,
                    "forecast_days": 3,
                    "timezone": "UTC",
                }
                resp_f = await client.get(OPEN_METEO_FORECAST_URL, params=f_params)
                resp_f.raise_for_status()
                forecast_data = resp_f.json()
                sources.append("Open-Meteo Forecast API")
            except Exception as exc:
                logger.warning(f"Open-Meteo Forecast API failed for ({latitude}, {longitude}): {exc}")
                warnings.append(f"Open-Meteo Forecast API unavailable: {exc}")

            # 2. Open-Meteo Historical Archive API (32 days ago up to 5 days ago)
            try:
                end_d = (date.today() - timedelta(days=5)).isoformat()
                start_d = (date.today() - timedelta(days=32)).isoformat()
                a_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_d,
                    "end_date": end_d,
                    "hourly": "precipitation",
                    "timezone": "UTC",
                }
                resp_a = await client.get(OPEN_METEO_ARCHIVE_URL, params=a_params)
                resp_a.raise_for_status()
                archive_data = resp_a.json()
                sources.append("Open-Meteo Historical Archive API")
            except Exception as exc:
                logger.warning(f"Open-Meteo Archive API failed for ({latitude}, {longitude}): {exc}")
                warnings.append(f"Open-Meteo Historical Archive API unavailable: {exc}")

        # Parse current observation
        current_info: Dict[str, Any] = {
            "precipitation_mm": None,
            "temperature_c": None,
            "relative_humidity_pct": None,
            "wind_speed_kmh": None,
            "weather_code": None,
            "weather_condition": "Unavailable",
            "observation_time": None,
            "is_stale": True,
        }

        ref_time = now_utc
        if forecast_data and isinstance(forecast_data.get("current"), dict):
            cur = forecast_data["current"]
            obs_time_str = cur.get("time")
            is_stale = False
            if obs_time_str:
                obs_dt = _parse_utc_hour(obs_time_str)
                ref_time = obs_dt
                age_hours = (now_utc - obs_dt).total_seconds() / 3600.0
                if age_hours > STALE_OBSERVATION_HOURS:
                    is_stale = True
                    warnings.append(f"Current weather observation is stale ({age_hours:.1f}h old).")
            wcode = cur.get("weather_code")
            current_info = {
                "precipitation_mm": cur.get("precipitation"),
                "temperature_c": cur.get("temperature_2m"),
                "relative_humidity_pct": cur.get("relative_humidity_2m"),
                "wind_speed_kmh": cur.get("wind_speed_10m"),
                "weather_code": wcode,
                "weather_condition": WMO_WEATHER_CODES.get(wcode, f"WMO Code {wcode}" if wcode is not None else "Unknown"),
                "observation_time": obs_time_str,
                "is_stale": is_stale,
            }

            if obs_time_str:
                try:
                    save_weather_observation(
                        {
                            "id": f"wx_{uuid.uuid4().hex[:12]}",
                            "location_id": loc_id,
                            "latitude": latitude,
                            "longitude": longitude,
                            "precipitation": current_info["precipitation_mm"],
                            "temperature": current_info["temperature_c"],
                            "humidity": current_info["relative_humidity_pct"],
                            "wind_speed": current_info["wind_speed_kmh"],
                            "weather_code": wcode,
                            "observation_time": obs_time_str,
                            "source": "Open-Meteo Forecast API",
                            "created_at": now_utc.isoformat(),
                        }
                    )
                except Exception as exc:
                    logger.warning(f"Failed to persist weather observation: {exc}")

        # Merge hourly records strictly into observed (<= ref_time) vs forecast (> ref_time)
        observed_hourly: Dict[datetime, Optional[float]] = {}
        forecast_hourly: Dict[datetime, Optional[float]] = {}

        if archive_data and isinstance(archive_data.get("hourly"), dict):
            times = archive_data["hourly"].get("time", [])
            precips = archive_data["hourly"].get("precipitation", [])
            for t_str, p_val in zip(times, precips):
                dt = _parse_utc_hour(t_str)
                if dt <= ref_time:
                    observed_hourly[dt] = float(p_val) if p_val is not None else None

        if forecast_data and isinstance(forecast_data.get("hourly"), dict):
            times = forecast_data["hourly"].get("time", [])
            precips = forecast_data["hourly"].get("precipitation", [])
            for t_str, p_val in zip(times, precips):
                dt = _parse_utc_hour(t_str)
                val = float(p_val) if p_val is not None else None
                if dt <= ref_time:
                    # Forecast API past_days fills recent 5 days where archive lags
                    if dt not in observed_hourly or observed_hourly[dt] is None:
                        observed_hourly[dt] = val
                else:
                    forecast_hourly[dt] = val

        bundle = {
            "location_id": loc_id,
            "latitude": latitude,
            "longitude": longitude,
            "reference_time_utc": ref_time.isoformat(),
            "retrieved_at": now_utc.isoformat(),
            "cached": False,
            "sources": sources,
            "current": current_info,
            "observed_hourly": observed_hourly,
            "forecast_hourly": forecast_hourly,
            "forecast_available": forecast_data is not None and len(forecast_hourly) > 0,
            "archive_available": archive_data is not None,
            "warnings": warnings,
        }

        # Only cache if at least one Open-Meteo endpoint succeeded
        if sources:
            self._cache[cache_key] = (now_mono, bundle)

        return bundle


weather_service = WeatherService()
