import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

import numpy as np

from app.db.database import save_rainfall_analysis

# Configurable thresholds (provisional engineering defaults; require regional calibration for NE India)
AWI_DECAY_K = float(os.getenv("AWI_DECAY_K", "0.85"))
RAIN_REF_1H_MM = float(os.getenv("RAIN_REF_1H_MM", "30.0"))
RAIN_REF_24H_MM = float(os.getenv("RAIN_REF_24H_MM", "100.0"))
RAIN_REF_72H_MM = float(os.getenv("RAIN_REF_72H_MM", "180.0"))
RAIN_REF_AWI_MM = float(os.getenv("RAIN_REF_AWI_MM", "150.0"))

OBSERVED_WINDOWS_HOURS: Dict[str, int] = {
    "1h": 1,
    "3h": 3,
    "6h": 6,
    "24h": 24,
    "72h": 72,
    "7d": 168,
    "15d": 360,
    "30d": 720,
}

FORECAST_WINDOWS_HOURS: Dict[str, int] = {
    "next_3h": 3,
    "next_6h": 6,
    "next_24h": 24,
    "next_72h": 72,
}


def _compute_window_sum(
    hourly_series: Dict[datetime, Optional[float]],
    start_dt: datetime,
    end_dt: datetime,
    expected_hours: int,
    contains_forecast: bool,
) -> Dict[str, Any]:
    """
    Sum precipitation over (start_dt, end_dt] using actual timestamps.
    Missing/None records are NEVER silently treated as 0.0.
    """
    valid_vals: List[float] = []
    for ts, val in hourly_series.items():
        if start_dt < ts <= end_dt and val is not None:
            valid_vals.append(float(val))

    valid_hours = len(valid_vals)
    is_complete = valid_hours >= expected_hours
    total_mm = round(float(sum(valid_vals)), 2) if valid_hours > 0 else None

    return {
        "rainfall_mm": total_mm,
        "valid_hours": valid_hours,
        "expected_hours": expected_hours,
        "is_complete": is_complete,
        "contains_forecast": contains_forecast,
    }


def analyze_rainfall(
    weather_bundle: Dict[str, Any],
    decay_k: Optional[float] = None,
    persist: bool = True,
) -> Dict[str, Any]:
    """
    Convert raw Open-Meteo observed & forecast hourly series into:
    - Observed rolling accumulations (1h, 3h, 6h, 24h, 72h, 7d, 15d, 30d)
    - Rainfall intensity indicators
    - Antecedent Wetness Index (AWI) proxy
    - Forecast rainfall concern (next 3h, 6h, 24h, 72h)
    - Normalized 0-100 observed & forecast rainfall subscores
    """
    k = decay_k if decay_k is not None else AWI_DECAY_K
    ref_time = datetime.fromisoformat(weather_bundle["reference_time_utc"])
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)

    observed_hourly: Dict[datetime, Optional[float]] = weather_bundle.get("observed_hourly", {})
    forecast_hourly: Dict[datetime, Optional[float]] = weather_bundle.get("forecast_hourly", {})
    warnings: List[str] = list(weather_bundle.get("warnings", []))

    # A. Observed rolling rainfall windows
    observed_windows: Dict[str, Dict[str, Any]] = {}
    for label, hours in OBSERVED_WINDOWS_HOURS.items():
        win_stat = _compute_window_sum(
            observed_hourly,
            start_dt=ref_time - timedelta(hours=hours),
            end_dt=ref_time,
            expected_hours=hours,
            contains_forecast=False,
        )
        win_stat["window"] = label
        observed_windows[label] = win_stat
        if not win_stat["is_complete"]:
            warnings.append(
                f"Observed {label} window incomplete ({win_stat['valid_hours']}/{hours} valid hours)."
            )

    # B. Rainfall intensity indicators (from observed data only)
    obs_24h_vals = [
        float(v) for ts, v in observed_hourly.items()
        if (ref_time - timedelta(hours=24)) < ts <= ref_time and v is not None
    ]
    max_hourly_24h = round(max(obs_24h_vals), 2) if obs_24h_vals else None

    # Max 3-hour rolling sum within last 24h
    max_3h_24h: Optional[float] = None
    if len(obs_24h_vals) >= 3:
        sorted_24h = sorted(
            [(ts, float(v)) for ts, v in observed_hourly.items() if (ref_time - timedelta(hours=24)) < ts <= ref_time and v is not None],
            key=lambda x: x[0],
        )
        rolling_3 = [
            sum(x[1] for x in sorted_24h[i : i + 3])
            for i in range(len(sorted_24h) - 2)
        ]
        max_3h_24h = round(max(rolling_3), 2) if rolling_3 else None

    # Max 24-hour daily sum within last 7 days
    daily_totals: Dict[str, float] = {}
    for ts, v in observed_hourly.items():
        if (ref_time - timedelta(days=30)) < ts <= ref_time and v is not None:
            day_key = ts.date().isoformat()
            daily_totals[day_key] = daily_totals.get(day_key, 0.0) + float(v)

    last_7_days = [(ref_time.date() - timedelta(days=i)).isoformat() for i in range(7)]
    last_7_vals = [daily_totals[d] for d in last_7_days if d in daily_totals]
    max_24h_7d = round(max(last_7_vals), 2) if last_7_vals else None

    intensity = {
        "max_hourly_24h_mm": max_hourly_24h,
        "max_3h_24h_mm": max_3h_24h,
        "max_24h_7d_mm": max_24h_7d,
        "heavy_rainfall_detected": bool(
            (max_hourly_24h is not None and max_hourly_24h >= 15.0)
            or (observed_windows["24h"]["rainfall_mm"] is not None and observed_windows["24h"]["rainfall_mm"] >= 50.0)
        ),
    }

    # C. Antecedent Wetness Index (AWI): AWI(t) = P(t) + k * AWI(t-1)
    awi_value: Optional[float] = None
    if daily_totals:
        sorted_days = sorted(daily_totals.keys())
        awi = 0.0
        for d in sorted_days:
            awi = daily_totals[d] + k * awi
        awi_value = round(awi, 2)

    awi_proxy = {
        "awi_value": awi_value,
        "decay_coefficient_k": k,
        "days_evaluated": len(daily_totals),
        "proxy_disclaimer": "Rainfall-based antecedent wetness proxy only; NOT a measured soil moisture value.",
    }

    # D. Forecast rainfall concern (strictly separated from observed)
    forecast_windows: Dict[str, Dict[str, Any]] = {}
    for label, hours in FORECAST_WINDOWS_HOURS.items():
        win_stat = _compute_window_sum(
            forecast_hourly,
            start_dt=ref_time,
            end_dt=ref_time + timedelta(hours=hours),
            expected_hours=hours,
            contains_forecast=True,
        )
        win_stat["window"] = label
        forecast_windows[label] = win_stat

    # E. Configurable Rainfall Subscores (0-100) avoiding double-counting
    observed_score: Optional[float] = None
    obs_components: List[float] = []
    if max_hourly_24h is not None:
        obs_components.append(min(100.0, (max_hourly_24h / RAIN_REF_1H_MM) * 100.0))
    if observed_windows["24h"]["rainfall_mm"] is not None:
        obs_components.append(min(100.0, (observed_windows["24h"]["rainfall_mm"] / RAIN_REF_24H_MM) * 100.0))
    if awi_value is not None:
        obs_components.append(min(100.0, (awi_value / RAIN_REF_AWI_MM) * 100.0))

    if obs_components:
        # Use weighted blend of peak intensity/24h and AWI rather than summing all correlated windows
        peak_short = max(obs_components[:2]) if len(obs_components) >= 2 else obs_components[0]
        awi_comp = obs_components[-1] if awi_value is not None else peak_short
        observed_score = round(0.6 * peak_short + 0.4 * awi_comp, 2)

    forecast_score: Optional[float] = None
    f24 = forecast_windows["next_24h"]["rainfall_mm"]
    f72 = forecast_windows["next_72h"]["rainfall_mm"]
    if f24 is not None or f72 is not None:
        f24_s = min(100.0, ((f24 or 0.0) / RAIN_REF_24H_MM) * 100.0) if f24 is not None else 0.0
        f72_s = min(100.0, ((f72 or 0.0) / RAIN_REF_72H_MM) * 100.0) if f72 is not None else 0.0
        forecast_score = round(max(f24_s, f72_s), 2)

    overall_rain_score: Optional[float] = None
    if observed_score is not None and forecast_score is not None:
        overall_rain_score = round(0.65 * observed_score + 0.35 * forecast_score, 2)
    elif observed_score is not None:
        overall_rain_score = observed_score
    elif forecast_score is not None:
        overall_rain_score = forecast_score

    # Completeness fraction across key windows (24h, 72h, 7d, 30d)
    key_wins = [observed_windows[w] for w in ("24h", "72h", "7d", "30d")]
    completeness = round(
        sum(min(1.0, w["valid_hours"] / w["expected_hours"]) for w in key_wins) / len(key_wins),
        3,
    )

    calculated_at = datetime.now(timezone.utc).isoformat()
    result = {
        "location_id": weather_bundle["location_id"],
        "latitude": weather_bundle["latitude"],
        "longitude": weather_bundle["longitude"],
        "observed_windows": observed_windows,
        "forecast_windows": forecast_windows,
        "intensity": intensity,
        "awi_proxy": awi_proxy,
        "observed_rainfall_score": observed_score,
        "forecast_rainfall_score": forecast_score,
        "rainfall_concern_score": overall_rain_score,
        "data_completeness": completeness,
        "calculated_at": calculated_at,
        "warnings": warnings,
        "calibration_note": (
            "Rainfall thresholds (1h=30mm, 24h=100mm, 72h=180mm, AWI=150mm, k=0.85) are "
            "provisional engineering defaults requiring regional calibration for North Eastern India."
        ),
    }

    if persist:
        try:
            save_rainfall_analysis(
                {
                    "id": f"rain_{uuid.uuid4().hex[:12]}",
                    "location_id": weather_bundle["location_id"],
                    "rainfall_1h": observed_windows["1h"]["rainfall_mm"],
                    "rainfall_3h": observed_windows["3h"]["rainfall_mm"],
                    "rainfall_6h": observed_windows["6h"]["rainfall_mm"],
                    "rainfall_24h": observed_windows["24h"]["rainfall_mm"],
                    "rainfall_72h": observed_windows["72h"]["rainfall_mm"],
                    "rainfall_7d": observed_windows["7d"]["rainfall_mm"],
                    "rainfall_15d": observed_windows["15d"]["rainfall_mm"],
                    "rainfall_30d": observed_windows["30d"]["rainfall_mm"],
                    "awi_value": awi_value,
                    "forecast_rainfall": f24,
                    "data_completeness": completeness,
                    "calculated_at": calculated_at,
                }
            )
        except Exception:
            pass

    return result
