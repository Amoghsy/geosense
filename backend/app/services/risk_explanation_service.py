from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.db.database import (
    get_risk_by_assessment_id,
    get_risk_assessments_chronological,
    save_risk_explanation,
)

FACTOR_LABELS: Dict[str, str] = {
    "observed_rainfall": "Observed Rainfall & AWI Proxy",
    "forecast_rainfall": "Upcoming Forecast Rainfall",
    "baseline_susceptibility": "Baseline Multimodal Susceptibility (Phase 2)",
    "terrain": "Terrain & Slope Attributes",
    "satellite_detection": "Satellite Landslide Evidence (Phase 1 Prithvi)",
}

SCIENTIFIC_DISCLAIMER = (
    "GeoSense provides a rule-based heuristic risk index (0-100) for decision support only. "
    "It is NOT a calibrated landslide probability; a high score does not guarantee a landslide, "
    "a low score does not guarantee safety, missing satellite imagery does not mean no landslide exists, "
    "and AWI is a rainfall-based wetness proxy rather than measured soil moisture."
)


def _status_from_score(score: Optional[float]) -> str:
    if score is None:
        return "Unavailable"
    if score >= 75.0:
        return "Critical"
    if score >= 50.0:
        return "High"
    if score >= 25.0:
        return "Elevated"
    return "Low"


def _direction_from_score(score: Optional[float]) -> str:
    if score is None:
        return "unavailable"
    return "increased_risk" if score >= 25.0 else "reduced_risk"


class RiskExplanationService:
    """
    Phase 5 Explainable AI (XAI) & Risk Trend Service.
    Directly explains the Phase 3 weighted-rule risk engine using stored assessment records.
    """

    def build_factor_breakdown(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        factor_scores: Dict[str, Optional[float]] = record.get("factor_scores", {})
        cfg_weights: Dict[str, float] = record.get("factor_weights_configured", {})
        eff_weights: Dict[str, float] = record.get("factor_weights_effective", {})
        freshness: Dict[str, Any] = record.get("data_freshness", {})

        rain = record.get("rainfall_indicators") or {}
        obs = rain.get("observed_windows", {})
        fc = rain.get("forecast_windows", {})
        awi = rain.get("awi_proxy", {})
        susc = record.get("susceptibility_info") or {}
        terr = record.get("terrain_info") or {}
        sat = record.get("satellite_detection_evidence") or {}

        raw_map = {
            "observed_rainfall": {
                "raw": {
                    "rainfall_24h_mm": obs.get("24h", {}).get("rainfall_mm"),
                    "rainfall_72h_mm": obs.get("72h", {}).get("rainfall_mm"),
                    "rainfall_7d_mm": obs.get("7d", {}).get("rainfall_mm"),
                    "rainfall_15d_mm": obs.get("15d", {}).get("rainfall_mm"),
                    "awi_proxy_mm": awi.get("awi_value"),
                    "max_hourly_24h_mm": rain.get("intensity", {}).get("max_hourly_24h_mm"),
                },
                "source": "Open-Meteo Forecast & Historical Archive APIs",
                "timestamp": freshness.get("weather_observation_time"),
                "stale": freshness.get("weather_is_stale"),
            },
            "forecast_rainfall": {
                "raw": {
                    "next_24h_mm": fc.get("next_24h", {}).get("rainfall_mm"),
                    "next_72h_mm": fc.get("next_72h", {}).get("rainfall_mm"),
                },
                "source": "Open-Meteo Forecast API",
                "timestamp": freshness.get("weather_observation_time"),
                "stale": freshness.get("weather_is_stale"),
            },
            "baseline_susceptibility": {
                "raw": (
                    {
                        "susceptibility_score_01": susc.get("susceptibility_score_01"),
                        "susceptibility_class": susc.get("susceptibility_class"),
                        "coverage_status": susc.get("coverage_status"),
                    }
                    if susc.get("available") else None
                ),
                "source": susc.get("model_repository", "vinukatashidu/landslide-detection-multimodal"),
                "timestamp": susc.get("created_at"),
                "stale": False if susc.get("available") else None,
            },
            "terrain": {
                "raw": (
                    {"elevation_m": terr.get("elevation_m"), "slope_deg": terr.get("slope_deg")}
                    if terr.get("available") else None
                ),
                "source": "User/GIS Terrain Elevation & Slope",
                "timestamp": record.get("assessment_time"),
                "stale": False if terr.get("available") else None,
            },
            "satellite_detection": {
                "raw": (
                    {
                        "landslide_detected": sat.get("landslide_detected"),
                        "landslide_pixel_percentage": sat.get("landslide_pixel_percentage"),
                        "age_days": sat.get("age_days"),
                    }
                    if sat.get("available") else None
                ),
                "source": sat.get("model", "srivassid/prithvi-landslide"),
                "timestamp": sat.get("timestamp"),
                "stale": (sat.get("age_days") is not None and sat.get("age_days") > 14.0) if sat.get("available") else None,
            },
        }

        factors: List[Dict[str, Any]] = []
        for key, label in FACTOR_LABELS.items():
            norm_score = factor_scores.get(key)
            cfg_w = float(cfg_weights.get(key, 0.0))
            eff_w = float(eff_weights.get(key, 0.0))
            avail = norm_score is not None
            contrib = round(norm_score * eff_w, 2) if avail else None
            meta = raw_map[key]

            factors.append(
                {
                    "factor_key": key,
                    "factor_label": label,
                    "availability_status": "available" if avail else "unavailable",
                    "status_label": _status_from_score(norm_score),
                    "direction": _direction_from_score(norm_score),
                    "raw_value": meta["raw"],
                    "normalized_score": norm_score,
                    "configured_weight": cfg_w,
                    "effective_weight": eff_w,
                    "contribution_points": contrib,
                    "data_source": meta["source"] if avail else None,
                    "data_timestamp": meta["timestamp"],
                    "is_stale": meta["stale"],
                }
            )
        return factors

    def explain_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        record = get_risk_by_assessment_id(assessment_id)
        if not record:
            return None

        factors = self.build_factor_breakdown(record)
        increasing = [f["factor_label"] for f in factors if f["direction"] == "increased_risk"]
        reducing = [f["factor_label"] for f in factors if f["direction"] == "reduced_risk"]
        unavailable = [f["factor_label"] for f in factors if f["direction"] == "unavailable"]

        # Sort available factors by contribution_points descending
        available_sorted = sorted(
            [f for f in factors if f["contribution_points"] is not None],
            key=lambda x: x["contribution_points"],
            reverse=True,
        )
        top_desc = (
            ", ".join(f"{f['factor_label']} (+{f['contribution_points']} pts, {f['status_label']})" for f in available_sorted[:2])
            if available_sorted else "no valid factors"
        )

        cat = record.get("risk_category", "UNKNOWN")
        score = record.get("risk_score")
        comp = record.get("completeness_score", 0.0)
        ts = record.get("assessment_time")
        loc_name = record.get("location_name") or record.get("location_id")

        if cat == "INSUFFICIENT_DATA":
            text = (
                f"The selected location ({loc_name}) has an INSUFFICIENT_DATA status as of {ts}. "
                f"Unavailable factors: {', '.join(unavailable)}. No fallback risk score was fabricated."
            )
        else:
            missing_part = (
                f" Unavailable factors excluded from weighting: {', '.join(unavailable)} (completeness {comp*100:.0f}%)."
                if unavailable else f" All configured factors were available (completeness {comp*100:.0f}%)."
            )
            stale_note = (
                " Note: Weather observation data is marked stale."
                if record.get("data_freshness", {}).get("weather_is_stale") else ""
            )
            text = (
                f"The selected area ({loc_name}) currently has a {cat} landslide risk index "
                f"({score}/100) as of {ts}. The primary contributors to this weighted index are: {top_desc}."
                f"{missing_part}{stale_note} This heuristic index is not a calibrated probability of landslide occurrence."
            )

        save_risk_explanation(
            {
                "assessment_id": assessment_id,
                "location_id": record["location_id"],
                "factor_contributions": factors,
                "increasing_factors": increasing,
                "reducing_factors": reducing,
                "unavailable_factors": unavailable,
                "explanation_text": text,
                "data_reliability": {
                    "completeness_score": comp,
                    "freshness": record.get("data_freshness", {}),
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return {
            "assessment_id": assessment_id,
            "location_id": record["location_id"],
            "location_name": record.get("location_name"),
            "risk_score": score,
            "risk_category": cat,
            "is_calibrated_probability": False,
            "completeness_score": comp,
            "increasing_factors": increasing,
            "reducing_factors": reducing,
            "unavailable_factors": unavailable,
            "factor_contributions": factors,
            "missing_factors": record.get("missing_factors", []),
            "data_freshness": record.get("data_freshness", {}),
            "explanation": text,
            "scientific_disclaimer": SCIENTIFIC_DISCLAIMER,
            "assessment_time": ts,
        }

    def analyze_trends(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        records = get_risk_assessments_chronological(location_id, start_date=start_date, end_date=end_date)
        if not records:
            return {
                "location_id": location_id,
                "start_date": start_date,
                "end_date": end_date,
                "assessment_count": 0,
                "insufficient_history": True,
                "message": "No stored risk assessments found for this location and date range.",
                "timeline": [],
                "category_changes": [],
                "significant_shifts": [],
            }

        eff_loc_id = records[0]["location_id"]
        timeline: List[Dict[str, Any]] = []
        category_changes: List[Dict[str, Any]] = []
        significant_shifts: List[Dict[str, Any]] = []

        prev_rec = None
        for r in records:
            rain = r.get("rainfall_indicators") or {}
            obs = rain.get("observed_windows", {})
            fc = rain.get("forecast_windows", {})
            timeline.append(
                {
                    "assessment_id": r["assessment_id"],
                    "assessment_time": r["assessment_time"],
                    "risk_score": r.get("risk_score"),
                    "risk_category": r.get("risk_category"),
                    "rainfall_24h_mm": obs.get("24h", {}).get("rainfall_mm"),
                    "rainfall_72h_mm": obs.get("72h", {}).get("rainfall_mm"),
                    "forecast_24h_mm": fc.get("next_24h", {}).get("rainfall_mm"),
                    "awi_proxy_mm": rain.get("awi_proxy", {}).get("awi_value"),
                    "completeness_score": r.get("completeness_score"),
                }
            )
            if prev_rec is not None:
                if prev_rec.get("risk_category") != r.get("risk_category"):
                    category_changes.append(
                        {
                            "timestamp": r["assessment_time"],
                            "from_category": prev_rec.get("risk_category"),
                            "to_category": r.get("risk_category"),
                            "assessment_id": r["assessment_id"],
                        }
                    )
                s1 = prev_rec.get("risk_score")
                s2 = r.get("risk_score")
                if s1 is not None and s2 is not None and abs(s2 - s1) >= 5.0:
                    significant_shifts.append(
                        {
                            "timestamp": r["assessment_time"],
                            "direction": "increased" if s2 > s1 else "decreased",
                            "delta": round(s2 - s1, 2),
                            "from_score": s1,
                            "to_score": s2,
                        }
                    )
            prev_rec = r

        insufficient = len(records) < 2
        msg = (
            "Insufficient historical assessments (< 2) to establish a multi-point trend; displaying single stored record."
            if insufficient else f"Retrieved {len(records)} real stored assessments for trend analysis."
        )
        return {
            "location_id": eff_loc_id,
            "start_date": start_date,
            "end_date": end_date,
            "assessment_count": len(records),
            "insufficient_history": insufficient,
            "message": msg,
            "timeline": timeline,
            "category_changes": category_changes,
            "significant_shifts": significant_shifts,
        }

    def compare_assessments(
        self,
        location_id: str,
        assessment_id_1: str,
        assessment_id_2: str,
    ) -> Optional[Dict[str, Any]]:
        r1 = get_risk_by_assessment_id(assessment_id_1)
        r2 = get_risk_by_assessment_id(assessment_id_2)
        if not r1 or not r2:
            return None

        s1 = r1.get("risk_score")
        s2 = r2.get("risk_score")
        score_delta = round(s2 - s1, 2) if (s1 is not None and s2 is not None) else None
        cat_changed = r1.get("risk_category") != r2.get("risk_category")

        b1 = {f["factor_key"]: f for f in self.build_factor_breakdown(r1)}
        b2 = {f["factor_key"]: f for f in self.build_factor_breakdown(r2)}

        factor_deltas: List[Dict[str, Any]] = []
        changed_drivers: List[str] = []
        for k, label in FACTOR_LABELS.items():
            c1 = b1[k]["contribution_points"]
            c2 = b2[k]["contribution_points"]
            delta = round(c2 - c1, 2) if (c1 is not None and c2 is not None) else None
            factor_deltas.append(
                {
                    "factor_key": k,
                    "factor_label": label,
                    "contribution_1": c1,
                    "contribution_2": c2,
                    "contribution_delta": delta,
                    "score_1": b1[k]["normalized_score"],
                    "score_2": b2[k]["normalized_score"],
                }
            )
            if delta is not None and abs(delta) >= 1.0:
                word = "increased" if delta > 0 else "decreased"
                changed_drivers.append(f"{label} {word} by {abs(delta):.2f} pts")

        def _rain_val(rec: Dict[str, Any], win: str, forecast: bool = False) -> Optional[float]:
            ri = rec.get("rainfall_indicators") or {}
            grp = ri.get("forecast_windows" if forecast else "observed_windows", {})
            return grp.get(win, {}).get("rainfall_mm")

        r24_1, r24_2 = _rain_val(r1, "24h"), _rain_val(r2, "24h")
        f24_1, f24_2 = _rain_val(r1, "next_24h", True), _rain_val(r2, "next_24h", True)
        rainfall_deltas = {
            "observed_24h_delta_mm": round(r24_2 - r24_1, 2) if (r24_1 is not None and r24_2 is not None) else None,
            "forecast_24h_delta_mm": round(f24_2 - f24_1, 2) if (f24_1 is not None and f24_2 is not None) else None,
        }

        if score_delta is None:
            comp_text = "Comparison incomplete because one or both assessments lacked a valid risk score."
        else:
            trend_word = "increased" if score_delta > 0 else ("decreased" if score_delta < 0 else "remained unchanged")
            drivers_str = "; ".join(changed_drivers) if changed_drivers else "no individual factor shifted by >= 1.0 pt"
            comp_text = (
                f"The risk index {trend_word} by {score_delta:+.2f} points "
                f"(from {s1} [{r1.get('risk_category')}] to {s2} [{r2.get('risk_category')}]). "
                f"Key factor changes: {drivers_str}."
            )

        return {
            "location_id": r2.get("location_id", location_id),
            "assessment_1": {
                "assessment_id": assessment_id_1,
                "risk_score": s1,
                "risk_category": r1.get("risk_category"),
                "assessment_time": r1.get("assessment_time"),
            },
            "assessment_2": {
                "assessment_id": assessment_id_2,
                "risk_score": s2,
                "risk_category": r2.get("risk_category"),
                "assessment_time": r2.get("assessment_time"),
            },
            "score_delta": score_delta,
            "category_changed": cat_changed,
            "factor_deltas": factor_deltas,
            "rainfall_deltas": rainfall_deltas,
            "comparison_explanation": comp_text,
        }


risk_explanation_service = RiskExplanationService()
