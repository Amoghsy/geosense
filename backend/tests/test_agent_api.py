import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_agent_ui_and_health():
    ui = client.get("/agent-ui")
    assert ui.status_code == 200
    assert "text/html" in ui.headers["content-type"]

    h = client.get("/agent/health")
    assert h.status_code == 200
    data = h.json()
    assert data["status"] == "healthy"
    assert data["google_adk_installed"] is True
    assert "weather_analysis_tool" in data["available_tools"]
    assert "landslide_risk_analysis_tool" in data["available_tools"]


def test_agent_grounded_qa_and_followup_session_memory():
    # Turn 1: Ask about Shillong risk (triggers real Open-Meteo + Phase 3 risk engine)
    r1 = client.post(
        "/agent/chat",
        json={
            "message": "What is the current landslide risk in Shillong?",
            "role": "citizen",
        },
    )
    assert r1.status_code == 200
    d1 = r1.json()
    sid = d1["session_id"]
    assert "landslide_risk_analysis_tool" in d1["tools_used"]
    assert d1["structured_data"]["risk_summary"]["risk_category"] in {
        "LOW", "MODERATE", "HIGH", "CRITICAL", "INSUFFICIENT_DATA"
    }
    assert "not a calibrated probability" in d1["reply"]

    # Turn 2: Follow-up without repeating location (uses session memory!)
    r2 = client.post(
        "/agent/chat",
        json={
            "message": "Why is it at this level and is rain expected?",
            "session_id": sid,
            "role": "citizen",
        },
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["session_id"] == sid
    assert "risk_explanation_tool" in d2["tools_used"]
    assert "weather_analysis_tool" in d2["tools_used"]
    assert "factor_contributions" in d2["structured_data"]
    assert "rainfall_summary" in d2["structured_data"]

    # Turn 3: Check session history retrieval
    hist = client.get(f"/agent/sessions/{sid}", params={"role": "citizen"})
    assert hist.status_code == 200
    assert len(hist.json()["messages"]) == 4


def test_agent_role_based_access_controls():
    # Create a field_officer session
    s_resp = client.post(
        "/agent/sessions",
        json={"role": "field_officer", "user_id": "officer_1"},
    )
    assert s_resp.status_code == 200
    sid = s_resp.json()["session_id"]

    # Citizen cannot access field_officer session
    forbidden_sess = client.get(f"/agent/sessions/{sid}", params={"role": "citizen"})
    assert forbidden_sess.status_code == 403

    # Citizen cannot generate situation report
    forbidden_sr = client.post(
        "/agent/situation-report",
        json={"region_id": "meghalaya", "role": "citizen"},
    )
    assert forbidden_sr.status_code == 403

    # Authority CAN generate situation report
    auth_sr = client.post(
        "/agent/situation-report",
        json={"region_id": "meghalaya", "latitude": 25.5788, "longitude": 91.8933, "role": "authority"},
    )
    assert auth_sr.status_code == 200
    sr_data = auth_sr.json()
    assert sr_data["authorized"] is True
    assert "weather_snapshot" in sr_data
    assert "gis_summary" in sr_data


def test_agent_missing_satellite_and_invalid_session():
    r = client.post(
        "/agent/chat",
        json={
            "message": "Are there any satellite detections in Gangtok?",
            "role": "field_officer",
        },
    )
    assert r.status_code == 200
    assert "satellite_detection_tool" in r.json()["tools_used"]

    # Invalid session ID -> 404
    bad = client.post(
        "/agent/chat",
        json={"message": "Hello", "session_id": "sess_does_not_exist", "role": "citizen"},
    )
    assert bad.status_code == 404
