import os
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.db.database import (
    get_db_connection,
    ensure_phase9_schema,
    get_risk_by_assessment_id,
    get_risk_assessments_chronological,
)
from app.services.gis_service import gis_service

ALERT_RAIN_24H_THRESHOLD_MM = float(os.getenv("ALERT_RAIN_24H_MM", "60.0"))
ALERT_FORECAST_24H_THRESHOLD_MM = float(os.getenv("ALERT_FORECAST_24H_MM", "75.0"))
ALERT_SCORE_DELTA_THRESHOLD = float(os.getenv("ALERT_SCORE_DELTA", "15.0"))


class AlertGenerationService:
    """
    Generates PENDING_REVIEW alert recommendations from real Phase 3 risk assessments
    and verified Phase 8 incidents. Prevents duplicate alerts via dedup_key.
    Never generates alerts from INSUFFICIENT_DATA.
    """

    def _insert_alert_if_new(self, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            dup = conn.execute(
                "SELECT alert_id FROM alerts WHERE dedup_key = ? AND approval_status IN ('PENDING_REVIEW', 'APPROVED', 'PUBLISHED')",
                (alert_data["dedup_key"],),
            ).fetchone()
            if dup:
                return None

            conn.execute(
                """
                INSERT INTO alerts (
                    alert_id, alert_type, severity, title, description,
                    location_id, location_name, latitude, longitude, state, district,
                    assessment_id, supporting_evidence_json, source, approval_status,
                    is_official_public_warning, dedup_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', 0, ?, ?, ?)
                """,
                (
                    alert_data["alert_id"],
                    alert_data["alert_type"],
                    alert_data["severity"],
                    alert_data["title"],
                    alert_data["description"],
                    alert_data.get("location_id"),
                    alert_data.get("location_name"),
                    alert_data.get("latitude"),
                    alert_data.get("longitude"),
                    alert_data.get("state"),
                    alert_data.get("district"),
                    alert_data.get("assessment_id"),
                    json.dumps(alert_data.get("supporting_evidence", {})),
                    alert_data["source"],
                    alert_data["dedup_key"],
                    alert_data["created_at"],
                    alert_data["created_at"],
                ),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_data["alert_id"],)).fetchone()
            return dict(row)
        finally:
            conn.close()

    def evaluate_risk_assessment(self, assessment_id: str) -> List[Dict[str, Any]]:
        rec = get_risk_by_assessment_id(assessment_id)
        if not rec or rec.get("risk_category") == "INSUFFICIENT_DATA" or rec.get("risk_score") is None:
            return []

        loc_id = rec["location_id"]
        cat = rec["risk_category"]
        score = float(rec["risk_score"])
        lat = rec["latitude"]
        lon = rec["longitude"]
        state = gis_service._find_state_for_point(lat, lon)
        loc_name = rec.get("location_name") or loc_id
        today_str = datetime.now(timezone.utc).date().isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()

        generated: List[Dict[str, Any]] = []

        # Rule A & B: Risk Escalation or Elevated Category (HIGH / CRITICAL)
        history = get_risk_assessments_chronological(loc_id, limit=10)
        prev_rec = history[-2] if len(history) >= 2 and history[-1]["assessment_id"] == assessment_id else None
        escalated = False
        delta = 0.0
        if prev_rec and prev_rec.get("risk_score") is not None:
            delta = score - float(prev_rec["risk_score"])
            if prev_rec.get("risk_category") != cat and cat in {"HIGH", "CRITICAL"}:
                escalated = True
            elif delta >= ALERT_SCORE_DELTA_THRESHOLD:
                escalated = True

        if cat in {"HIGH", "CRITICAL"} or escalated:
            sev = "CRITICAL" if cat == "CRITICAL" else "WARNING"
            created = self._insert_alert_if_new(
                {
                    "alert_id": f"alr_{uuid.uuid4().hex[:12]}",
                    "alert_type": "RISK_ESCALATION",
                    "severity": sev,
                    "title": f"{cat} Heuristic Landslide Risk — {loc_name}",
                    "description": (
                        f"Risk index reached {score}/100 ({cat}). "
                        + (f"Score increased by +{delta:.1f} pts vs prior assessment. " if escalated and delta > 0 else "")
                        + "Heuristic decision-support alert awaiting authority review; not a calibrated probability."
                    ),
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "latitude": lat,
                    "longitude": lon,
                    "state": state,
                    "assessment_id": assessment_id,
                    "supporting_evidence": {"risk_score": score, "risk_category": cat, "delta": round(delta, 2)},
                    "source": "Phase 3 Dynamic Risk Engine",
                    "dedup_key": f"RISK_ESCALATION:{loc_id}:{cat}:{today_str}",
                    "created_at": now_iso,
                }
            )
            if created:
                generated.append(created)

        # Rule C: Rainfall threshold (Observed vs Forecast kept strictly distinct)
        rain = rec.get("rainfall_indicators") or {}
        obs_24 = rain.get("observed_windows", {}).get("24h", {}).get("rainfall_mm")
        fc_24 = rain.get("forecast_windows", {}).get("next_24h", {}).get("rainfall_mm")
        if (obs_24 is not None and obs_24 >= ALERT_RAIN_24H_THRESHOLD_MM) or (
            fc_24 is not None and fc_24 >= ALERT_FORECAST_24H_THRESHOLD_MM
        ):
            created_r = self._insert_alert_if_new(
                {
                    "alert_id": f"alr_{uuid.uuid4().hex[:12]}",
                    "alert_type": "HEAVY_RAINFALL",
                    "severity": "WARNING",
                    "title": f"Heavy Rainfall Trigger — {loc_name}",
                    "description": (
                        f"Observed 24h rainfall: {obs_24 if obs_24 is not None else 'N/A'} mm; "
                        f"Forecast next 24h rainfall: {fc_24 if fc_24 is not None else 'N/A'} mm."
                    ),
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "latitude": lat,
                    "longitude": lon,
                    "state": state,
                    "assessment_id": assessment_id,
                    "supporting_evidence": {"observed_24h_mm": obs_24, "forecast_24h_mm": fc_24},
                    "source": "Open-Meteo Rainfall Analyzer",
                    "dedup_key": f"HEAVY_RAINFALL:{loc_id}:{today_str}",
                    "created_at": now_iso,
                }
            )
            if created_r:
                generated.append(created_r)

        return generated

    def evaluate_verified_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        ensure_phase9_schema()
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM incidents WHERE id = ? AND status = 'VERIFIED'", (incident_id,)).fetchone()
            if not row:
                return []
            inc = dict(row)
        finally:
            conn.close()

        today_str = datetime.now(timezone.utc).date().isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()
        loc_name = inc.get("location_name") or f"({inc['latitude']:.3f}, {inc['longitude']:.3f})"
        created = self._insert_alert_if_new(
            {
                "alert_id": f"alr_{uuid.uuid4().hex[:12]}",
                "alert_type": "VERIFIED_INCIDENT",
                "severity": "WARNING",
                "title": f"Verified {inc['incident_category']} Incident — {loc_name}",
                "description": inc.get("description") or "Verified field incident.",
                "location_id": None,
                "location_name": loc_name,
                "latitude": inc["latitude"],
                "longitude": inc["longitude"],
                "state": inc.get("state"),
                "district": inc.get("district"),
                "assessment_id": None,
                "supporting_evidence": {"incident_id": incident_id, "verified_by": inc.get("verified_by")},
                "source": "GeoSense Verified Field Incident",
                "dedup_key": f"VERIFIED_INCIDENT:{incident_id}:{today_str}",
                "created_at": now_iso,
            }
        )
        return [created] if created else []


alert_generation_service = AlertGenerationService()
