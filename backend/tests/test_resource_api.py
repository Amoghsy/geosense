import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)


def test_resources_ui_endpoint():
    resp = client.get("/resources-ui")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_resource_lifecycle_verification_and_role_access():
    # 1. Citizen cannot create a resource -> 403
    c_forb = client.post(
        "/resources?role=citizen",
        json={
            "resource_name": "Test Facility",
            "resource_type": "HOSPITAL",
            "latitude": 25.576,
            "longitude": 91.882,
        },
    )
    assert c_forb.status_code == 403

    # 2. Field officer registers a candidate hospital (starts PENDING & UNKNOWN)
    create_resp = client.post(
        "/resources?role=field_officer",
        json={
            "resource_name": "Test Shillong Hospital Fixture",
            "resource_type": "HOSPITAL",
            "state": "Meghalaya",
            "district": "East Khasi Hills",
            "latitude": 25.5760,
            "longitude": 91.8820,
            "contact_number": "+91-0000-000001",
            "is_public_contact": False,
            "capacity": None,
        },
    )
    assert create_resp.status_code == 201
    res = create_resp.json()
    rid = res["resource_id"]
    assert res["verification_status"] == "PENDING"
    assert res["operational_status"] == "UNKNOWN"
    assert res["availability_status"] == "UNKNOWN"
    assert res["capacity"] is None

    # 3. Citizen cannot see PENDING resource
    assert client.get(f"/resources/{rid}?role=citizen").status_code == 404

    # 4. Field officer cannot verify (Authority only) -> 403
    assert client.post(
        f"/resources/{rid}/verify?role=field_officer",
        json={"verification_status": "VERIFIED"},
    ).status_code == 403

    # 5. Authority verifies resource and sets operational & availability
    ver_resp = client.post(
        f"/resources/{rid}/verify?role=authority",
        json={
            "verification_status": "VERIFIED",
            "operational_status": "OPERATIONAL",
            "availability_status": "LIMITED",
            "notes": "Confirmed via test fixture",
        },
    )
    assert ver_resp.status_code == 200
    assert ver_resp.json()["verification_status"] == "VERIFIED"
    assert ver_resp.json()["last_verified_at"] is not None

    # 6. Citizen now sees VERIFIED resource, but private contact is redacted
    cit_get = client.get(f"/resources/{rid}?role=citizen")
    assert cit_get.status_code == 200
    assert "Restricted" in cit_get.json()["contact_number"]

    # 7. Edit & availability update + history check
    patch_resp = client.patch(
        f"/resources/{rid}?role=authority",
        json={"description": "Updated trauma fixture"},
    )
    assert patch_resp.status_code == 200

    avail_resp = client.patch(
        f"/resources/{rid}/availability?role=authority",
        json={"availability_status": "AVAILABLE", "capacity": 50, "current_occupancy": 10},
    )
    assert avail_resp.status_code == 200
    assert avail_resp.json()["remaining_capacity"] == 40

    hist_resp = client.get(f"/resources/{rid}/history?role=authority")
    assert hist_resp.status_code == 200
    assert hist_resp.json()["count"] >= 4

    # 8. Nearby spatial search, radius filtering, and recommendations
    near = client.get(
        "/resources/near",
        params={"latitude": 25.5788, "longitude": 91.8933, "radius_km": 10.0, "resource_type": "HOSPITAL"},
    )
    assert near.status_code == 200
    n_data = near.json()
    assert n_data["distance_type"] == "straight_line_haversine_km"
    assert any(r["resource_id"] == rid for r in n_data["resources"])

    rec = client.get("/resources/recommend", params={"latitude": 25.5788, "longitude": 91.8933, "radius_km": 25.0})
    assert rec.status_code == 200
    assert rec.json()["count"] >= 1

    # 9. GIS layer displays verified resource
    gis_res = client.get("/gis/layers/emergency_resources/features")
    assert gis_res.status_code == 200
    assert gis_res.json()["returned_count"] >= 1

    # 10. Phase 6 AI agent retrieves real verified resource
    chat_resp = client.post(
        "/agent/chat",
        json={"message": "Which verified hospitals are near Shillong?", "role": "citizen"},
    )
    assert chat_resp.status_code == 200
    assert "nearby_resource_finder_tool" in chat_resp.json()["tools_used"]
    assert chat_resp.json()["structured_data"]["nearby_resources"]["count"] >= 1


def test_rejected_resource_and_invalid_coordinates():
    r_bad = client.post(
        "/resources?role=authority",
        json={
            "resource_name": "Invalid Facility",
            "resource_type": "SHELTER",
            "latitude": 120.0,
            "longitude": 91.8,
        },
    )
    assert r_bad.status_code == 422

    # Register & reject a shelter
    cr = client.post(
        "/resources?role=authority",
        json={
            "resource_name": "Rejected Shelter Fixture",
            "resource_type": "SHELTER",
            "latitude": 25.58,
            "longitude": 91.89,
        },
    ).json()
    rej = client.post(
        f"/resources/{cr['resource_id']}/verify?role=authority",
        json={"verification_status": "REJECTED", "operational_status": "CLOSED", "availability_status": "UNAVAILABLE"},
    )
    assert rej.status_code == 200
    assert client.get(f"/resources/{cr['resource_id']}?role=citizen").status_code == 404

    stats = client.get("/resources/statistics?role=authority")
    assert stats.status_code == 200
    assert stats.json()["rejected_resources"] >= 1
