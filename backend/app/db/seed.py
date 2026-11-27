import json
import logging
from datetime import datetime, timezone, timedelta

from app.db.database import (
    get_db_connection,
    init_db,
    ensure_phase7_resource_schema,
    ensure_phase8_schema,
    ensure_phase9_schema,
)
from app.services.auth_service import hash_password
from app.services.weather_service import make_location_id

logger = logging.getLogger("geosense.seed")


def seed_database() -> None:
    """
    Idempotently seed realistic Meghalaya GeoSense data into SQLite:
    - Citizen, Field Officer (FO-1027, FO-2048), and Authority accounts
    - Risk assessments, weather observations, rainfall analyses, and XAI explanations
    - Verified emergency resources (shelters, hospitals, rescue teams, relief centres)
    - Citizen & officer incident reports and field inspections
    - Published alerts and in-app notifications
    """
    init_db()
    ensure_phase7_resource_schema()
    ensure_phase8_schema()
    ensure_phase9_schema()

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    conn = get_db_connection()

    try:
        # 1. Seed Users (Citizen, Field Officers, Authority)
        users = [
            (
                "usr_seed_citizen_aiban",
                "aiban@geosense.in",
                hash_password("password123"),
                "Aiban Khonglah",
                "+91 98630 01482",
                "CITIZEN",
                "Meghalaya",
                "East Khasi Hills",
                None,
                1,
                now_iso,
            ),
            (
                "usr_seed_fo_1027",
                "fo1027@geosense.in",
                hash_password("password123"),
                "Riban Khongwir",
                "+91 98630 11027",
                "FIELD_OFFICER",
                "Meghalaya",
                "East Khasi Hills",
                "FO-1027",
                1,
                now_iso,
            ),
            (
                "usr_seed_fo_2048",
                "fo2048@geosense.in",
                hash_password("password123"),
                "Dapmain Lyngdoh",
                "+91 98630 12048",
                "FIELD_OFFICER",
                "Meghalaya",
                "East Khasi Hills (Mawsynram)",
                "FO-2048",
                1,
                now_iso,
            ),
            (
                "usr_seed_authority",
                "authority@geosense.in",
                hash_password("password123"),
                "SDMA Command Director",
                "+91 36422 25000",
                "AUTHORITY",
                "Meghalaya",
                None,
                "AUTH-01",
                1,
                now_iso,
            ),
        ]
        for u in users:
            conn.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id, email, password_hash, full_name, phone, role,
                    assigned_state, assigned_district, officer_code, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                u,
            )

        # 2. Seed Risk Assessments, Weather Observations, Rainfall Analyses & XAI Explanations
        locations = [
            {
                "name": "Cherrapunji, Meghalaya",
                "lat": 25.2702,
                "lon": 91.7323,
                "score": 84.0,
                "cat": "CRITICAL",
                "rain_24h": 112.4,
                "forecast_24h": 86.0,
                "temp": 18.5,
                "humidity": 96.0,
                "wind": 22.0,
                "weather_code": 65,
                "slope": 32.0,
                "soil": 0.44,
                "explanation": "Prolonged heavy monsoon rainfall (112.4 mm in 24h) combined with steep 32-degree slopes and saturated soil elevates landslide susceptibility.",
                "factors": {
                    "observed_rainfall": 88.0,
                    "forecast_rainfall": 82.0,
                    "susceptibility": 84.0,
                    "terrain": 78.0,
                    "satellite_detection": 72.0,
                },
            },
            {
                "name": "Sohra Slope · S1 (SH-5)",
                "lat": 25.2845,
                "lon": 91.7210,
                "score": 88.0,
                "cat": "CRITICAL",
                "rain_24h": 118.0,
                "forecast_24h": 92.5,
                "temp": 18.0,
                "humidity": 97.0,
                "wind": 24.5,
                "weather_code": 65,
                "slope": 36.0,
                "soil": 0.46,
                "explanation": "Critical slope instability along SH-5 corridor driven by intense rainfall and antecedent soil saturation.",
                "factors": {
                    "observed_rainfall": 92.0,
                    "forecast_rainfall": 86.0,
                    "susceptibility": 88.0,
                    "terrain": 84.0,
                    "satellite_detection": 76.0,
                },
            },
            {
                "name": "Mawsynram, Meghalaya",
                "lat": 25.2975,
                "lon": 91.5826,
                "score": 71.0,
                "cat": "HIGH",
                "rain_24h": 94.2,
                "forecast_24h": 74.0,
                "temp": 19.0,
                "humidity": 95.0,
                "wind": 19.0,
                "weather_code": 63,
                "slope": 28.0,
                "soil": 0.39,
                "explanation": "High cumulative rainfall and moderate-to-steep road cuts indicate elevated landslide risk.",
                "factors": {
                    "observed_rainfall": 78.0,
                    "forecast_rainfall": 72.0,
                    "susceptibility": 70.0,
                    "terrain": 66.0,
                    "satellite_detection": 55.0,
                },
            },
            {
                "name": "Pynursla · NH-206",
                "lat": 25.3119,
                "lon": 91.9016,
                "score": 49.0,
                "cat": "MODERATE",
                "rain_24h": 54.0,
                "forecast_24h": 42.0,
                "temp": 20.2,
                "humidity": 89.0,
                "wind": 14.0,
                "weather_code": 61,
                "slope": 24.0,
                "soil": 0.32,
                "explanation": "Moderate rainfall with localized road debris clearance underway along NH-206.",
                "factors": {
                    "observed_rainfall": 54.0,
                    "forecast_rainfall": 48.0,
                    "susceptibility": 50.0,
                    "terrain": 46.0,
                    "satellite_detection": 35.0,
                },
            },
            {
                "name": "Shillong, Meghalaya",
                "lat": 25.5788,
                "lon": 91.8933,
                "score": 31.0,
                "cat": "MODERATE",
                "rain_24h": 28.5,
                "forecast_24h": 22.0,
                "temp": 21.5,
                "humidity": 84.0,
                "wind": 11.0,
                "weather_code": 61,
                "slope": 18.0,
                "soil": 0.27,
                "explanation": "Moderate urban drainage runoff with low-to-moderate slope hazard.",
                "factors": {
                    "observed_rainfall": 32.0,
                    "forecast_rainfall": 28.0,
                    "susceptibility": 34.0,
                    "terrain": 30.0,
                    "satellite_detection": 20.0,
                },
            },
        ]

        weights = {
            "observed_rainfall": 0.30,
            "forecast_rainfall": 0.20,
            "susceptibility": 0.25,
            "terrain": 0.15,
            "satellite_detection": 0.10,
        }

        for idx, loc in enumerate(locations):
            loc_id = make_location_id(loc["lat"], loc["lon"])
            obs_id = f"wobs_seed_{idx:02d}"
            rain_id = f"rain_seed_{idx:02d}"

            conn.execute(
                """
                INSERT OR IGNORE INTO weather_observations (
                    id, location_id, latitude, longitude, precipitation,
                    temperature, humidity, wind_speed, weather_code,
                    observation_time, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    obs_id,
                    loc_id,
                    loc["lat"],
                    loc["lon"],
                    loc["rain_24h"] / 24.0,
                    loc["temp"],
                    loc["humidity"],
                    loc["wind"],
                    loc["weather_code"],
                    now_iso,
                    "Open-Meteo / IMD Seed",
                    now_iso,
                ),
            )

            conn.execute(
                """
                INSERT OR IGNORE INTO rainfall_analyses (
                    id, location_id, rainfall_1h, rainfall_3h, rainfall_6h,
                    rainfall_24h, rainfall_72h, rainfall_7d, rainfall_15d,
                    rainfall_30d, awi_value, forecast_rainfall,
                    data_completeness, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rain_id,
                    loc_id,
                    round(loc["rain_24h"] * 0.12, 1),
                    round(loc["rain_24h"] * 0.28, 1),
                    round(loc["rain_24h"] * 0.45, 1),
                    loc["rain_24h"],
                    round(loc["rain_24h"] * 2.1, 1),
                    round(loc["rain_24h"] * 3.8, 1),
                    round(loc["rain_24h"] * 6.4, 1),
                    round(loc["rain_24h"] * 10.2, 1),
                    round(loc["rain_24h"] * 1.35, 1),
                    loc["forecast_24h"],
                    1.0,
                    now_iso,
                ),
            )

            # Seed 3 historical snapshots + latest snapshot for trend charts
            for step_hours, score_offset in [(72, -16), (24, -7), (6, -3), (0, 0)]:
                ts = (now - timedelta(hours=step_hours)).isoformat()
                ass_id = f"risk_seed_{idx:02d}_{step_hours}h"
                sc = max(5.0, min(98.0, loc["score"] + score_offset))
                cat = (
                    "CRITICAL" if sc >= 75 else
                    "HIGH" if sc >= 50 else
                    "MODERATE" if sc >= 25 else
                    "LOW"
                )
                payload = {
                    "assessment_id": ass_id,
                    "location_id": loc_id,
                    "location_name": loc["name"],
                    "latitude": loc["lat"],
                    "longitude": loc["lon"],
                    "risk_score": sc,
                    "risk_category": cat,
                    "factor_scores": loc["factors"],
                    "factor_weights_effective": weights,
                    "missing_factors": [],
                    "explanation": loc["explanation"],
                    "assessment_time": ts,
                    "data_freshness": {"weather": "live", "terrain": "static_dem"},
                    "completeness_score": 1.0,
                    "slope_deg": loc["slope"],
                    "soil_moisture_m3_m3": loc["soil"],
                    "rainfall_24h_mm": loc["rain_24h"],
                    "forecast_24h_mm": loc["forecast_24h"],
                }
                conn.execute(
                    """
                    INSERT OR IGNORE INTO risk_assessments (
                        id, location_id, latitude, longitude, risk_score,
                        risk_category, factor_scores, factor_weights, missing_factors,
                        explanation, assessment_time, data_sources, completeness_score,
                        raw_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ass_id,
                        loc_id,
                        loc["lat"],
                        loc["lon"],
                        sc,
                        cat,
                        json.dumps(loc["factors"]),
                        json.dumps(weights),
                        json.dumps([]),
                        loc["explanation"],
                        ts,
                        json.dumps(["Open-Meteo", "Prithvi-EO-2.0", "SRTM-DEM"]),
                        1.0,
                        json.dumps(payload),
                    ),
                )

                if step_hours == 0:
                    contributions = [
                        {
                            "factor": "Heavy Rainfall (24h)",
                            "raw_score": loc["factors"]["observed_rainfall"],
                            "weight": weights["observed_rainfall"],
                            "weighted_contribution": round(loc["factors"]["observed_rainfall"] * weights["observed_rainfall"], 2),
                            "impact": "INCREASING",
                        },
                        {
                            "factor": "Slope & Susceptibility",
                            "raw_score": loc["factors"]["susceptibility"],
                            "weight": weights["susceptibility"],
                            "weighted_contribution": round(loc["factors"]["susceptibility"] * weights["susceptibility"], 2),
                            "impact": "INCREASING",
                        },
                        {
                            "factor": "Forecast Rainfall",
                            "raw_score": loc["factors"]["forecast_rainfall"],
                            "weight": weights["forecast_rainfall"],
                            "weighted_contribution": round(loc["factors"]["forecast_rainfall"] * weights["forecast_rainfall"], 2),
                            "impact": "INCREASING",
                        },
                        {
                            "factor": "Terrain Steepness",
                            "raw_score": loc["factors"]["terrain"],
                            "weight": weights["terrain"],
                            "weighted_contribution": round(loc["factors"]["terrain"] * weights["terrain"], 2),
                            "impact": "INCREASING",
                        },
                        {
                            "factor": "Satellite Detection",
                            "raw_score": loc["factors"]["satellite_detection"],
                            "weight": weights["satellite_detection"],
                            "weighted_contribution": round(loc["factors"]["satellite_detection"] * weights["satellite_detection"], 2),
                            "impact": "NEUTRAL",
                        },
                    ]
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO risk_explanations (
                            assessment_id, location_id, factor_contributions_json,
                            increasing_factors_json, reducing_factors_json,
                            unavailable_factors_json, explanation_text,
                            data_reliability_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ass_id,
                            loc_id,
                            json.dumps(contributions),
                            json.dumps(["Heavy Rainfall (24h)", "Slope & Susceptibility", "Forecast Rainfall"]),
                            json.dumps([]),
                            json.dumps([]),
                            loc["explanation"],
                            json.dumps({"completeness": 1.0, "confidence": "HIGH"}),
                            now_iso,
                        ),
                    )

        # 3. Seed Verified Emergency Resources in Meghalaya
        resources = [
            (
                "res_seed_shelter_a",
                "SHELTER",
                "Community Shelter A",
                "Community Shelter A",
                25.2750,
                91.7380,
                "meghalaya",
                "Mawmluh Road, Cherrapunji",
                "Meghalaya",
                "East Khasi Hills",
                "+91 36372 35100",
                1,
                150,
                66,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "Primary community evacuation shelter with backup power and clean water.",
            ),
            (
                "res_seed_govt_school",
                "SHELTER",
                "Government School Shelter",
                "Government School Shelter",
                25.2810,
                91.7450,
                "meghalaya",
                "Upper Sohra Main Road",
                "Meghalaya",
                "East Khasi Hills",
                "+91 36372 35112",
                1,
                200,
                80,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "Designated monsoon relief shelter at Government Higher Secondary School.",
            ),
            (
                "res_seed_hospital",
                "HOSPITAL",
                "District Hospital Sohra",
                "District Hospital Sohra",
                25.2880,
                91.7200,
                "meghalaya",
                "Sohra CHC Complex, East Khasi Hills",
                "Meghalaya",
                "East Khasi Hills",
                "108",
                1,
                80,
                32,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "24-hour emergency trauma care and ambulance dispatch.",
            ),
            (
                "res_seed_rescue_north",
                "RESCUE_TEAM",
                "SDRF Rescue Team North",
                "SDRF Rescue Team North",
                25.2910,
                91.7310,
                "meghalaya",
                "Sohra Tactical Base, SH-5",
                "Meghalaya",
                "East Khasi Hills",
                "1070",
                1,
                24,
                0,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "Rapid response landslide clearance and medical evacuation unit.",
            ),
            (
                "res_seed_relief_centre",
                "RELIEF_CENTRE",
                "Relief Supply Centre",
                "Relief Supply Centre",
                25.2650,
                91.7500,
                "meghalaya",
                "Cherrapunji Block Office",
                "Meghalaya",
                "East Khasi Hills",
                "+91 36372 35220",
                1,
                500,
                120,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "Emergency food rations, drinking water, blankets, and first aid kits.",
            ),
            (
                "res_seed_shillong_hosp",
                "HOSPITAL",
                "Civil Hospital Shillong",
                "Civil Hospital Shillong",
                25.5750,
                91.8830,
                "meghalaya",
                "GS Road, Shillong",
                "Meghalaya",
                "East Khasi Hills",
                "+91 36422 24100",
                1,
                300,
                180,
                "AVAILABLE",
                "OPERATIONAL",
                "VERIFIED",
                "Tertiary emergency hospital and disaster referral centre.",
            ),
        ]
        for r in resources:
            conn.execute(
                """
                INSERT OR IGNORE INTO emergency_resources (
                    id, resource_type, name, resource_name, latitude, longitude,
                    region_id, address, state, district, contact_number,
                    is_public_contact, capacity, current_occupancy,
                    availability_status, operational_status, verification_status,
                    description, source, metadata_json, last_verified_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SDMA Seed', '{}', ?, ?, ?)
                """,
                (*r, now_iso, now_iso, now_iso),
            )

        # 4. Seed Incidents (Pending for officer verification + Verified for alerts/map)
        incidents = [
            (
                "inc_seed_01",
                "usr_seed_citizen_aiban",
                "citizen",
                "FALLING_ROCKS",
                "PENDING",
                25.2845,
                91.7210,
                "Large rocks have fallen onto the road near Sohra viewpoint. Only one lane is open. More debris is coming down.",
                "Sohra, SH-5",
                "Meghalaya",
                "East Khasi Hills",
                None,
                (now - timedelta(minutes=12)).isoformat(),
                "+91 98630 01482",
                "usr_seed_fo_1027",
                "meghalaya",
                (now - timedelta(minutes=12)).isoformat(),
                now_iso,
            ),
            (
                "inc_seed_02",
                "usr_seed_citizen_aiban",
                "citizen",
                "SLOPE_CRACKS",
                "PENDING",
                25.2975,
                91.5826,
                "Significant surface cracks observed stretching 15 meters along the mountain shoulder.",
                "Mawsynram",
                "Meghalaya",
                "East Khasi Hills",
                None,
                (now - timedelta(minutes=28)).isoformat(),
                "+91 98630 01482",
                "usr_seed_fo_2048",
                "meghalaya",
                (now - timedelta(minutes=28)).isoformat(),
                now_iso,
            ),
            (
                "inc_seed_03",
                "usr_seed_fo_1027",
                "officer",
                "ROAD_BLOCKAGE",
                "VERIFIED",
                25.3119,
                91.9016,
                "Debris cleared from one lane on NH-206 near Pynursla. Traffic moving slowly; proceed with caution.",
                "Pynursla road · NH-206",
                "Meghalaya",
                "East Khasi Hills",
                None,
                (now - timedelta(minutes=42)).isoformat(),
                "+91 98630 11027",
                "usr_seed_fo_1027",
                "meghalaya",
                (now - timedelta(minutes=42)).isoformat(),
                now_iso,
            ),
            (
                "inc_seed_04",
                "usr_seed_citizen_aiban",
                "citizen",
                "LANDSLIDE",
                "PENDING",
                25.2780,
                91.7280,
                "Fresh slope movement observed near Sohra slope S1 marker following intense morning rain.",
                "Sohra slope · S1",
                "Meghalaya",
                "East Khasi Hills",
                None,
                (now - timedelta(hours=1)).isoformat(),
                "+91 98630 01482",
                "usr_seed_fo_1027",
                "meghalaya",
                (now - timedelta(hours=1)).isoformat(),
                now_iso,
            ),
        ]
        for inc in incidents:
            conn.execute(
                """
                INSERT OR IGNORE INTO incidents (
                    id, reporter_user_id, reporter_type, incident_category, status,
                    latitude, longitude, description, location_name, state, district,
                    photo_path, incident_time, contact_info, assigned_officer_id,
                    region_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                inc,
            )

        # 5. Seed Field Inspections
        inspections = [
            (
                "insp_seed_01",
                "usr_seed_fo_1027",
                make_location_id(25.2780, 91.7280),
                25.2780,
                91.7280,
                "Sohra slope · S1",
                "Meghalaya",
                "East Khasi Hills",
                "IN_PROGRESS",
                "On-site slope stability & drainage inspection along SH-5 corridor.",
                "Assigned high-priority inspection.",
                None,
                1,
                88.0,
                "CRITICAL",
                (now - timedelta(hours=1)).isoformat(),
                now_iso,
            ),
            (
                "insp_seed_02",
                "usr_seed_fo_1027",
                make_location_id(25.2510, 91.6950),
                25.2510,
                91.6950,
                "Nongriat trail · Z3",
                "Meghalaya",
                "East Khasi Hills",
                "COMPLETED",
                "Trail retaining wall intact; minor surface runoff cleared.",
                "Risk assessment completed.",
                None,
                0,
                52.0,
                "HIGH",
                (now - timedelta(days=1)).isoformat(),
                (now - timedelta(days=1)).isoformat(),
            ),
            (
                "insp_seed_03",
                "usr_seed_fo_1027",
                make_location_id(25.4050, 91.7920),
                25.4050,
                91.7920,
                "Mawkdok slope · S4",
                "Meghalaya",
                "East Khasi Hills",
                "COMPLETED",
                "No fresh tension cracks observed; culvert clear.",
                "Site inspection completed.",
                None,
                0,
                38.0,
                "MODERATE",
                (now - timedelta(days=2)).isoformat(),
                (now - timedelta(days=2)).isoformat(),
            ),
        ]
        for insp in inspections:
            conn.execute(
                """
                INSERT OR IGNORE INTO field_inspections (
                    inspection_id, officer_id, location_id, latitude, longitude,
                    location_name, state, district, status, observations, inspection_notes,
                    photo_path, follow_up_required, risk_score_snapshot, risk_category_snapshot,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                insp,
            )

        # 6. Seed Published Alerts & Notifications
        alerts = [
            (
                "alr_seed_01",
                "HIGH_RISK",
                "CRITICAL",
                "HIGH LANDSLIDE RISK",
                "84% landslide risk index in Cherrapunji & Sohra SH-5. Avoid unstable slopes and mountain roads.",
                make_location_id(25.2702, 91.7323),
                "Cherrapunji · SH-5",
                25.2702,
                91.7323,
                "Meghalaya",
                "East Khasi Hills",
                "risk_seed_00_0h",
                json.dumps({"risk_score": 84.0, "rain_24h_mm": 112.4}),
                "GeoSense AI Early Warning",
                "PUBLISHED",
                "usr_seed_authority",
                "Published for East Khasi Hills citizens and field officers.",
                1,
                (now + timedelta(hours=24)).isoformat(),
                (now - timedelta(minutes=5)).isoformat(),
                "seed_cherrapunji_critical",
                (now - timedelta(minutes=5)).isoformat(),
                now_iso,
            ),
            (
                "alr_seed_02",
                "HEAVY_RAINFALL",
                "WARNING",
                "HEAVY RAINFALL WARNING",
                "Heavy rainfall (94+ mm/24h) expected across Mawsynram & Meghalaya East over the next 24 hours.",
                make_location_id(25.2975, 91.5826),
                "Mawsynram & Meghalaya East",
                25.2975,
                91.5826,
                "Meghalaya",
                "East Khasi Hills",
                "risk_seed_02_0h",
                json.dumps({"rain_24h_mm": 94.2, "forecast_24h_mm": 74.0}),
                "IMD / GeoSense Weather",
                "PUBLISHED",
                "usr_seed_authority",
                "Monsoon rainfall advisory.",
                1,
                (now + timedelta(hours=24)).isoformat(),
                (now - timedelta(minutes=18)).isoformat(),
                "seed_mawsynram_rain",
                (now - timedelta(minutes=18)).isoformat(),
                now_iso,
            ),
            (
                "alr_seed_03",
                "VERIFIED_INCIDENT",
                "WARNING",
                "ROAD BLOCKAGE UPDATE",
                "Partial blockage reported on NH-206 near Pynursla. One lane open; use alternate routes.",
                make_location_id(25.3119, 91.9016),
                "Pynursla · NH-206",
                25.3119,
                91.9016,
                "Meghalaya",
                "East Khasi Hills",
                None,
                json.dumps({"incident_id": "inc_seed_03"}),
                "PWD / Field Officer Verification",
                "PUBLISHED",
                "usr_seed_authority",
                "Verified road status update.",
                1,
                (now + timedelta(hours=12)).isoformat(),
                (now - timedelta(minutes=42)).isoformat(),
                "seed_pynursla_road",
                (now - timedelta(minutes=42)).isoformat(),
                now_iso,
            ),
            (
                "alr_seed_04",
                "EVACUATION_ADVISORY",
                "ADVISORY",
                "EVACUATION ADVISORY",
                "Residents near steep slopes in Sohra & Mawmluh should keep essentials ready and review shelter routes.",
                make_location_id(25.2750, 91.7380),
                "High-risk villages · Sohra",
                25.2750,
                91.7380,
                "Meghalaya",
                "East Khasi Hills",
                None,
                json.dumps({"nearest_shelter": "Community Shelter A"}),
                "Meghalaya SDMA",
                "PUBLISHED",
                "usr_seed_authority",
                "Preparedness advisory.",
                1,
                (now + timedelta(hours=48)).isoformat(),
                (now - timedelta(hours=1)).isoformat(),
                "seed_evacuation_advisory",
                (now - timedelta(hours=1)).isoformat(),
                now_iso,
            ),
        ]
        for alr in alerts:
            conn.execute(
                """
                INSERT OR IGNORE INTO alerts (
                    alert_id, alert_type, severity, title, description,
                    location_id, location_name, latitude, longitude, state, district,
                    assessment_id, supporting_evidence_json, source, approval_status,
                    approving_authority, admin_notes, is_official_public_warning,
                    expiry_at, published_at, dedup_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                alr,
            )

        # Seed in-app notifications for citizen & field officers
        target_users = [
            ("usr_seed_citizen_aiban", "CITIZEN"),
            ("usr_seed_fo_1027", "FIELD_OFFICER"),
            ("usr_seed_fo_2048", "FIELD_OFFICER"),
        ]
        for uid, role in target_users:
            for alr in alerts:
                nid = f"ntf_seed_{uid.split('_')[-1]}_{alr[0].split('_')[-1]}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO notifications (
                        notification_id, alert_id, recipient_user_id, recipient_role,
                        title, message, severity, is_read, is_acknowledged, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
                    """,
                    (nid, alr[0], uid, role, alr[3], alr[4], alr[2], alr[21]),
                )

        conn.commit()
        logger.info("GeoSense database seed completed successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
