import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.auth_service import ADMIN_PROVISION_SECRET
from app.ml.landslide_weather_analyzer import analyze_rainfall
from app.ml.landslide_risk_engine import compute_dynamic_risk
from app.services.email_notification_service import email_notification_service
from app.services.fcm_service import fcm_service

client = TestClient(app)


def test_alert_lifecycle_email_fcm_and_permissions():
    suf = uuid.uuid4().hex[:6]

    # Register Citizen (Meghalaya) and Authority
    cit = client.post(
        "/auth/register",
        json={"email": f"cit_{suf}@geosense.in", "password": "Password123!", "full_name": "Citizen One", "role": "CITIZEN"},
    ).json()
    cit_hdr = {"Authorization": f"Bearer {cit['access_token']}"}

    auth = client.post(
        "/auth/register",
        json={
            "email": f"auth_{suf}@geosense.in",
            "password": "Password123!",
            "full_name": "Authority One",
            "role": "AUTHORITY",
            "provision_secret": ADMIN_PROVISION_SECRET,
        },
    ).json()
    auth_hdr = {"Authorization": f"Bearer {auth['access_token']}"}

    # Citizen sets preferences & registers FCM device token
    pref = client.patch(
        "/notifications/preferences",
        headers=cit_hdr,
        json={"email_enabled": True, "push_enabled": True, "preferred_state": "Meghalaya"},
    )
    assert pref.status_code == 200
    dev = client.post(
        "/notifications/devices/register",
        headers=cit_hdr,
        json={"fcm_token": f"fake_fcm_token_{suf}_123456", "platform": "android"},
    )
    assert dev.status_code == 200
    dev_id = dev.json()["device_id"]

    # Create controlled high-rainfall + HIGH-risk synthetic assessment fixture
    ref = datetime.now(timezone.utc)
    bundle = {
        "location_id": f"loc_alr_{suf}",
        "latitude": 25.5788,
        "longitude": 91.8933,
        "reference_time_utc": ref.isoformat(),
        "retrieved_at": ref.isoformat(),
        "cached": False,
        "sources": ["Synthetic Test Fixture"],
        "current": {"observation_time": ref.isoformat(), "is_stale": False},
        "observed_hourly": {ref - timedelta(hours=i): 4.0 for i in range(24)},  # 96mm 24h (>60mm threshold)
        "forecast_hourly": {ref + timedelta(hours=i + 1): 3.5 for i in range(24)},  # 84mm fcst (>75mm)
        "warnings": [],
    }
    rain = analyze_rainfall(bundle, persist=False)
    assess = compute_dynamic_risk(
        25.5788, 91.8933, f"loc_alr_{suf}", "Shillong Alert Test", bundle, rain,
        elevation_m=1500.0, slope_deg=38.0, persist=True,
    )
    aid = assess["assessment_id"]

    # 1. Generate alert recommendations (Authority/Officer only)
    assert client.post("/alerts/generate", json={"assessment_id": aid}, headers=cit_hdr).status_code == 403
    gen = client.post("/alerts/generate", json={"assessment_id": aid}, headers=auth_hdr)
    assert gen.status_code == 201
    alerts = gen.json()["alerts"]
    assert len(alerts) >= 1
    alert_id = alerts[0]["alert_id"]
    assert alerts[0]["approval_status"] == "PENDING_REVIEW"

    # 2. Duplicate alert prevention
    gen_dup = client.post("/alerts/generate", json={"assessment_id": aid}, headers=auth_hdr)
    assert gen_dup.json()["count"] == 0

    # 3. Citizen cannot see unpublished alert or approve/publish it -> 403
    assert client.get(f"/alerts/{alert_id}", headers=cit_hdr).status_code == 403
    assert client.post(f"/alerts/{alert_id}/approve", json={}, headers=cit_hdr).status_code == 403
    assert client.post(f"/alerts/{alert_id}/publish", json={}, headers=cit_hdr).status_code == 403

    # 4. Authority approves & publishes with mocked SMTP + FCM provider
    app_resp = client.post(f"/alerts/{alert_id}/approve", json={"admin_notes": "Approved in test"}, headers=auth_hdr)
    assert app_resp.status_code == 200
    assert app_resp.json()["approval_status"] == "APPROVED"

    with patch.object(
        email_notification_service,
        "send_alert_email",
        return_value={
            "delivery_status": "SENT",
            "attempt_count": 1,
            "provider_message_id": "mock_smtp_1",
            "provider_response": "250 OK",
            "error_message": None,
        },
    ), patch.object(
        fcm_service,
        "send_push",
        return_value={
            "delivery_status": "SENT",
            "attempt_count": 1,
            "provider_message_id": "mock_fcm_1",
            "provider_response": "Accepted",
            "error_message": None,
        },
    ):
        pub_resp = client.post(f"/alerts/{alert_id}/publish", json={"admin_notes": "Publish test"}, headers=auth_hdr)
        assert pub_resp.status_code == 200
        pub_data = pub_resp.json()
        assert pub_data["alert"]["approval_status"] == "PUBLISHED"
        assert pub_data["delivery_summary"]["email"]["sent"] >= 1
        assert pub_data["delivery_summary"]["fcm_push"]["sent"] >= 1

    # 5. Check delivery history (only EMAIL and FCM_PUSH, no SMS)
    dels = client.get(f"/alerts/{alert_id}/deliveries", headers=auth_hdr).json()["deliveries"]
    channels = {d["channel"] for d in dels}
    assert channels.issubset({"EMAIL", "FCM_PUSH"})
    assert "SMS" not in channels

    # 6. Citizen receives in-app notification, marks read & acknowledges
    notifs = client.get("/notifications", headers=cit_hdr).json()["notifications"]
    matching = [n for n in notifs if n["alert_id"] == alert_id]
    assert len(matching) == 1
    nid = matching[0]["notification_id"]
    assert client.patch(f"/notifications/{nid}/read", headers=cit_hdr).json()["is_read"] == 1
    assert client.post(f"/alerts/{alert_id}/acknowledge", headers=cit_hdr).status_code == 200

    # 7. AI Agent read-only alert retrieval
    agent_r = client.post("/agent/chat", json={"message": "Show published alerts in Meghalaya", "role": "citizen"})
    assert agent_r.status_code == 200
    assert "read_alerts_tool" in agent_r.json()["tools_used"]

    # 8. Unregister device & test reject/cancel workflow
    assert client.delete(f"/notifications/devices/{dev_id}", headers=cit_hdr).status_code == 200
    assert client.post(f"/alerts/{alert_id}/cancel", json={"admin_notes": "All clear"}, headers=auth_hdr).json()["approval_status"] == "CANCELLED"


def test_unconfigured_smtp_and_fcm_graceful_failure():
    # Ensure unconfigured providers return FAILED without crashing
    e_res = email_notification_service.send_alert_email("user@example.com", {"alert_id": "a1", "title": "Test"}, "CITIZEN")
    assert e_res["delivery_status"] == "FAILED"
    f_res = fcm_service.send_push("fake_token_1234567890", {"alert_id": "a1", "title": "Test"})
    assert f_res["delivery_status"] == "FAILED"
