import os
import sys
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.ml.landslide_weather_analyzer import analyze_rainfall
from app.ml.landslide_risk_engine import compute_dynamic_risk, classify_risk_score

client = TestClient(app)


def _make_synthetic_bundle(
    obs_hourly_map,
    fc_hourly_map,
    ref_time=None,
    lat=25.5788,
    lon=91.8933,
    sources=None,
):
    """Deterministic synthetic test fixture for rainfall/risk unit tests."""
    ref = ref_time or datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
    return {
        "location_id": f"loc_{lat:.3f}_{lon:.3f}",
        "latitude": lat,
        "longitude": lon,
        "reference_time_utc": ref.isoformat(),
        "retrieved_at": ref.isoformat(),
        "cached": False,
        "sources": sources if sources is not None else ["Synthetic Test Fixture"],
        "current": {
            "precipitation_mm": 0.0,
            "temperature_c": 20.0,
            "relative_humidity_pct": 80,
            "wind_speed_kmh": 5.0,
            "weather_code": 0,
            "weather_condition": "Clear sky",
            "observation_time": ref.isoformat(),
            "is_stale": False,
        },
        "observed_hourly": obs_hourly_map,
        "forecast_hourly": fc_hourly_map,
        "forecast_available": len(fc_hourly_map) > 0,
        "archive_available": len(obs_hourly_map) > 0,
        "warnings": [],
    }


def test_risk_ui_endpoint():
    resp = client.get("/risk-ui")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "GeoSense" in resp.text


def test_live_open_meteo_current_and_rainfall_shillong():
    """Verify real Open-Meteo Forecast + Archive integration for Shillong, Meghalaya."""
    cur_resp = client.get("/weather/current", params={"latitude": 25.5788, "longitude": 91.8933})
    assert cur_resp.status_code == 200
    cur = cur_resp.json()
    assert cur["location_id"] == "loc_25.579_91.893"
    assert "Open-Meteo" in cur["source"]
    assert cur["temperature_c"] is not None

    rain_resp = client.get("/weather/rainfall", params={"latitude": 25.5788, "longitude": 91.8933})
    assert rain_resp.status_code == 200
    rain = rain_resp.json()
    for w in ("1h", "3h", "6h", "24h", "72h", "7d", "15d", "30d"):
        assert w in rain["observed_windows"]
        assert rain["observed_windows"][w]["contains_forecast"] is False
    for fw in ("next_3h", "next_6h", "next_24h", "next_72h"):
        assert fw in rain["forecast_windows"]
        assert rain["forecast_windows"][fw]["contains_forecast"] is True
    assert "NOT a measured soil moisture" in rain["awi_proxy"]["proxy_disclaimer"]


def test_synthetic_no_rainfall_and_heavy_rainfall():
    ref = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
    # 1. Zero rainfall fixture
    obs_zero = {ref - timedelta(hours=i): 0.0 for i in range(72)}
    fc_zero = {ref + timedelta(hours=i + 1): 0.0 for i in range(72)}
    b_zero = _make_synthetic_bundle(obs_zero, fc_zero, ref)
    r_zero = analyze_rainfall(b_zero, persist=False)
    assert r_zero["observed_windows"]["24h"]["rainfall_mm"] == 0.0
    assert r_zero["observed_windows"]["24h"]["is_complete"] is True
    assert r_zero["observed_rainfall_score"] == 0.0

    risk_zero = compute_dynamic_risk(
        25.5788, 91.8933, "loc_test_zero", "Test Zero", b_zero, r_zero, persist=False
    )
    assert risk_zero["risk_category"] == "LOW"
    assert risk_zero["risk_score"] == 0.0

    # 2. Heavy short-duration rainfall + heavy forecast fixture
    obs_heavy = {ref - timedelta(hours=i): (35.0 if i < 3 else 2.0) for i in range(72)}
    fc_heavy = {ref + timedelta(hours=i + 1): 5.0 for i in range(72)}
    b_heavy = _make_synthetic_bundle(obs_heavy, fc_heavy, ref)
    r_heavy = analyze_rainfall(b_heavy, persist=False)
    assert r_heavy["intensity"]["heavy_rainfall_detected"] is True
    assert r_heavy["observed_windows"]["3h"]["rainfall_mm"] == 105.0
    assert r_heavy["forecast_windows"]["next_24h"]["rainfall_mm"] == 120.0

    risk_heavy = compute_dynamic_risk(
        25.5788, 91.8933, "loc_test_heavy", "Test Heavy", b_heavy, r_heavy,
        elevation_m=1800.0, slope_deg=42.0, persist=False
    )
    assert risk_heavy["risk_category"] in {"HIGH", "CRITICAL"}
    assert risk_heavy["risk_score"] >= 70.0


def test_missing_hours_and_insufficient_data_handling():
    ref = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
    # Only 10 valid hours out of 24 -> must mark incomplete, NOT silently 0
    obs_partial = {ref - timedelta(hours=i): (None if i % 2 == 0 else 5.0) for i in range(24)}
    b_part = _make_synthetic_bundle(obs_partial, {}, ref)
    r_part = analyze_rainfall(b_part, persist=False)
    assert r_part["observed_windows"]["24h"]["is_complete"] is False
    assert r_part["observed_windows"]["24h"]["valid_hours"] == 12

    # Total weather failure -> INSUFFICIENT_DATA (no fabricated LOW fallback)
    b_empty = _make_synthetic_bundle({}, {}, ref, sources=[])
    r_empty = analyze_rainfall(b_empty, persist=False)
    risk_empty = compute_dynamic_risk(
        25.5788, 91.8933, "loc_empty", "Empty", b_empty, r_empty, persist=False
    )
    assert risk_empty["risk_category"] == "INSUFFICIENT_DATA"
    assert risk_empty["risk_score"] is None


def test_end_to_end_risk_analyze_history_explain_and_hotspots():
    resp = client.post(
        "/risk/analyze",
        json={
            "latitude": 25.5788,
            "longitude": 91.8933,
            "location_name": "Shillong, Meghalaya",
            "region_id": "meghalaya",
            "elevation_m": 1496.0,
            "slope_deg": 28.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_calibrated_probability"] is False
    assert data["risk_category"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert "observed_rainfall" in data["factor_weights_effective"]
    assert abs(sum(data["factor_weights_effective"].values()) - 1.0) < 1e-3
    assert "baseline_susceptibility" in data["missing_factors"]
    assert "satellite_detection" in data["missing_factors"]

    aid = data["assessment_id"]
    loc_id = data["location_id"]

    assert client.get(f"/risk/{loc_id}").status_code == 200
    exp = client.get(f"/risk/{aid}/explain")
    assert exp.status_code == 200
    assert data["risk_category"] in exp.json()["explanation"]

    hist = client.get(f"/risk/{aid}/history")
    assert hist.status_code == 200
    assert hist.json()["count"] >= 1

    hs = client.get("/risk/hotspots")
    assert hs.status_code == 200
