import os
import sys
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.risk_explanation_service import risk_explanation_service
from app.ml.landslide_risk_engine import compute_dynamic_risk
from app.ml.landslide_weather_analyzer import analyze_rainfall

client = TestClient(app)


def test_xai_ui_endpoint():
    resp = client.get("/xai-ui")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Chart" in resp.text


def test_real_assessment_explanation_and_contributions():
    # Create a real assessment via Phase 3
    a_resp = client.post(
        "/risk/analyze",
        json={
            "latitude": 25.5788,
            "longitude": 91.8933,
            "location_name": "Shillong, Meghalaya",
            "elevation_m": 1496.0,
            "slope_deg": 28.0,
        },
    )
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    aid = a_data["assessment_id"]
    loc_id = a_data["location_id"]

    # 1. Explanation endpoint
    exp_resp = client.get(f"/risk/{aid}/explanation")
    assert exp_resp.status_code == 200
    exp = exp_resp.json()
    assert exp["assessment_id"] == aid
    assert exp["is_calibrated_probability"] is False
    assert a_data["risk_category"] in exp["explanation"]
    assert len(exp["factor_contributions"]) == 5

    # Verify exact contribution math and missing factor handling
    total_pts = 0.0
    for f in exp["factor_contributions"]:
        if f["availability_status"] == "available":
            expected_pts = round(f["normalized_score"] * f["effective_weight"], 2)
            assert abs(f["contribution_points"] - expected_pts) <= 0.02
            total_pts += f["contribution_points"]
        else:
            assert f["normalized_score"] is None
            assert f["contribution_points"] is None

    assert abs(total_pts - a_data["risk_score"]) <= 0.1

    # 2. Contributing factors endpoint
    cf_resp = client.get(f"/risk/{aid}/contributing-factors")
    assert cf_resp.status_code == 200
    assert len(cf_resp.json()["factors"]) == 5

    # 3. GIS location -> assessment -> explanation integration
    gis_loc = client.get("/gis/location", params={"latitude": 25.5788, "longitude": 91.8933})
    assert gis_loc.status_code == 200
    assert gis_loc.json()["dynamic_risk"] is not None


def test_trends_comparison_and_stale_handling():
    # Create two controlled assessments for the same test location to test comparison & trends
    ref1 = datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)
    ref2 = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
    loc_id = "loc_test_xai_compare"

    b1 = {
        "location_id": loc_id, "latitude": 27.33, "longitude": 88.60,
        "reference_time_utc": ref1.isoformat(), "retrieved_at": ref1.isoformat(),
        "cached": False, "sources": ["Synthetic Fixture"],
        "current": {"observation_time": ref1.isoformat(), "is_stale": True},
        "observed_hourly": {ref1 - timedelta(hours=i): 0.2 for i in range(24)},
        "forecast_hourly": {ref1 + timedelta(hours=i + 1): 0.0 for i in range(24)},
        "warnings": [],
    }
    r1 = analyze_rainfall(b1, persist=False)
    a1 = compute_dynamic_risk(27.33, 88.60, loc_id, "Test XAI", b1, r1, elevation_m=1600.0, slope_deg=25.0, persist=True)

    b2 = {
        "location_id": loc_id, "latitude": 27.33, "longitude": 88.60,
        "reference_time_utc": ref2.isoformat(), "retrieved_at": ref2.isoformat(),
        "cached": False, "sources": ["Synthetic Fixture"],
        "current": {"observation_time": ref2.isoformat(), "is_stale": False},
        "observed_hourly": {ref2 - timedelta(hours=i): 15.0 for i in range(24)},
        "forecast_hourly": {ref2 + timedelta(hours=i + 1): 4.0 for i in range(24)},
        "warnings": [],
    }
    r2 = analyze_rainfall(b2, persist=False)
    a2 = compute_dynamic_risk(27.33, 88.60, loc_id, "Test XAI", b2, r2, elevation_m=1600.0, slope_deg=25.0, persist=True)

    # Stale weather check on a1
    exp1 = client.get(f"/risk/{a1['assessment_id']}/explanation").json()
    assert "stale" in exp1["explanation"].lower()

    # Trends endpoint
    tr = client.get(f"/risk/{loc_id}/trends")
    assert tr.status_code == 200
    tr_data = tr.json()
    assert tr_data["assessment_count"] >= 2
    assert tr_data["insufficient_history"] is False
    assert len(tr_data["significant_shifts"]) >= 1

    # Comparison endpoint
    cmp_resp = client.get(
        f"/risk/{loc_id}/comparison",
        params={"assessment_id_1": a1["assessment_id"], "assessment_id_2": a2["assessment_id"]},
    )
    assert cmp_resp.status_code == 200
    cmp_data = cmp_resp.json()
    assert cmp_data["score_delta"] > 0
    assert cmp_data["category_changed"] is True
    assert "increased" in cmp_data["comparison_explanation"]


def test_invalid_ids_handled_gracefully():
    assert client.get("/risk/nonexistent_id/explanation").status_code == 404
    assert client.get("/risk/nonexistent_id/contributing-factors").status_code == 404
    assert client.get(
        "/risk/loc_unknown/comparison",
        params={"assessment_id_1": "bad1", "assessment_id_2": "bad2"},
    ).status_code == 404

    tr_empty = client.get("/risk/loc_does_not_exist/trends")
    assert tr_empty.status_code == 200
    assert tr_empty.json()["insufficient_history"] is True
    assert tr_empty.json()["assessment_count"] == 0
