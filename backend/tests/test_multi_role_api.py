import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.auth_service import ADMIN_PROVISION_SECRET, create_access_token

client = TestClient(app)


def test_authority_ui_and_jwt_registration_security():
    assert client.get("/authority-ui").status_code == 200

    # 1. Citizen cannot register as AUTHORITY without provision_secret -> 403
    bad_reg = client.post(
        "/auth/register",
        json={
            "email": f"bad_{uuid.uuid4().hex[:6]}@geosense.in",
            "password": "Password123!",
            "full_name": "Unauthorized User",
            "role": "AUTHORITY",
        },
    )
    assert bad_reg.status_code == 403

    # 2. Unauthenticated /users/me -> 401
    assert client.get("/users/me").status_code == 401

    # 3. Expired token -> 401
    expired_tok = create_access_token(
        {"user_id": "usr_exp", "email": "e@e.com", "role": "CITIZEN"},
        expires_minutes=-5,
    )
    assert client.get("/users/me", headers={"Authorization": f"Bearer {expired_tok}"}).status_code == 401


def test_end_to_end_citizen_officer_authority_workflow():
    suffix = uuid.uuid4().hex[:6]

    # A. Register & Login Citizen
    cit_email = f"citizen_{suffix}@geosense.in"
    cit_reg = client.post(
        "/auth/register",
        json={"email": cit_email, "password": "Citizen@123", "full_name": "R. Kharkongor", "role": "CITIZEN"},
    )
    assert cit_reg.status_code == 201
    cit_tok = cit_reg.json()["access_token"]
    cit_hdr = {"Authorization": f"Bearer {cit_tok}"}

    # Profile update cannot escalate role
    prof = client.patch("/users/me", json={"full_name": "R. Kharkongor Updated"}, headers=cit_hdr)
    assert prof.status_code == 200
    assert prof.json()["role"] == "CITIZEN"

    # Citizen risk & dashboard
    assert client.get("/citizen/risk", params={"latitude": 25.5788, "longitude": 91.8933}).status_code == 200
    assert client.get("/citizen/dashboard", headers=cit_hdr).status_code == 200

    # Citizen submits incident report
    inc_resp = client.post(
        "/incidents",
        headers=cit_hdr,
        data={
            "incident_category": "SLOPE_CRACKS",
            "description": "Test fixture slope cracks observed near highway.",
            "latitude": "25.5788",
            "longitude": "91.8933",
            "location_name": "Shillong Bypass",
            "state": "Meghalaya",
        },
    )
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["incident_id"]
    assert inc_resp.json()["status"] == "PENDING"

    # Rapid duplicate submission -> 409
    dup_resp = client.post(
        "/incidents",
        headers=cit_hdr,
        data={
            "incident_category": "SLOPE_CRACKS",
            "description": "Duplicate test fixture",
            "latitude": "25.5788",
            "longitude": "91.8933",
        },
    )
    assert dup_resp.status_code == 409

    # Citizen sees own report, CANNOT verify it (403) or view officer/authority dashboards (403)
    assert client.get("/incidents/my-reports", headers=cit_hdr).json()["count"] >= 1
    assert client.post(f"/incidents/{inc_id}/verify", json={"status": "VERIFIED"}, headers=cit_hdr).status_code == 403
    assert client.get("/officer/dashboard", headers=cit_hdr).status_code == 403
    assert client.get("/authority/dashboard", headers=cit_hdr).status_code == 403

    # B. Provision Field Officer assigned to Meghalaya
    off_reg = client.post(
        "/auth/register",
        json={
            "email": f"officer_{suffix}@geosense.in",
            "password": "Officer@123",
            "full_name": "Officer M. Lyngdoh",
            "role": "FIELD_OFFICER",
            "assigned_state": "Meghalaya",
            "provision_secret": ADMIN_PROVISION_SECRET,
        },
    )
    assert off_reg.status_code == 201
    off_tok = off_reg.json()["access_token"]
    off_hdr = {"Authorization": f"Bearer {off_tok}"}

    # Cross-jurisdiction check: Meghalaya officer cannot query Sikkim incidents -> 403
    assert client.get("/officer/incidents", params={"state": "Sikkim"}, headers=off_hdr).status_code == 403

    # Officer dashboard & verification
    assert client.get("/officer/dashboard", headers=off_hdr).status_code == 200
    ver = client.post(
        f"/incidents/{inc_id}/verify",
        headers=off_hdr,
        json={"status": "VERIFIED", "verification_notes": "Confirmed on site"},
    )
    assert ver.status_code == 200
    assert ver.json()["status"] == "VERIFIED"

    # Officer submits & updates field inspection
    insp = client.post(
        "/inspections",
        headers=off_hdr,
        data={
            "latitude": "25.5788",
            "longitude": "91.8933",
            "observations": "Test fixture tension cracks 10m long",
            "state": "Meghalaya",
            "status": "IN_PROGRESS",
        },
    )
    assert insp.status_code == 201
    insp_id = insp.json()["inspection_id"]
    upd = client.patch(f"/inspections/{insp_id}", headers=off_hdr, json={"status": "COMPLETED", "follow_up_required": True})
    assert upd.status_code == 200
    assert upd.json()["status"] == "COMPLETED"

    # C. Provision Authority & verify Authority Dashboard, Analytics, Assignment, Situation Report, Audit Logs
    auth_reg = client.post(
        "/auth/register",
        json={
            "email": f"auth_{suffix}@geosense.in",
            "password": "Authority@123",
            "full_name": "SDMA Director",
            "role": "AUTHORITY",
            "provision_secret": ADMIN_PROVISION_SECRET,
        },
    )
    assert auth_reg.status_code == 201
    auth_hdr = {"Authorization": f"Bearer {auth_reg.json()['access_token']}"}

    assert client.get("/authority/dashboard", headers=auth_hdr).status_code == 200
    assert client.get("/authority/analytics", headers=auth_hdr).status_code == 200
    assert client.post(
        f"/authority/incidents/{inc_id}/assign",
        headers=auth_hdr,
        json={"officer_id": off_reg.json()["user"]["user_id"], "notes": "Priority check"},
    ).status_code == 200
    sr = client.post("/authority/situation-reports", headers=auth_hdr, json={"region_id": "meghalaya", "role": "authority"})
    assert sr.status_code == 200
    assert "report_id" in sr.json()
    assert client.get("/authority/audit-logs", headers=auth_hdr).json()["count"] >= 3
