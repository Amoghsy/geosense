import os
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("geosense.db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.getenv("GEOSENSE_DB_PATH", os.path.join(BASE_DIR, "geosense.db"))


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables for GeoSense Phase 2 susceptibility analyses."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS susceptibility_analyses (
                id TEXT PRIMARY KEY,
                region_id TEXT,
                latitude REAL,
                longitude REAL,
                input_metadata TEXT NOT NULL,
                model_repository TEXT NOT NULL,
                model_revision TEXT NOT NULL,
                prediction_output TEXT NOT NULL,
                susceptibility_value REAL,
                susceptibility_class TEXT,
                confidence REAL,
                source_metadata TEXT NOT NULL,
                coverage_status TEXT NOT NULL,
                processing_time REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_observations (
                id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                precipitation REAL,
                temperature REAL,
                humidity REAL,
                wind_speed REAL,
                weather_code INTEGER,
                observation_time TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(location_id, observation_time)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rainfall_analyses (
                id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL,
                rainfall_1h REAL,
                rainfall_3h REAL,
                rainfall_6h REAL,
                rainfall_24h REAL,
                rainfall_72h REAL,
                rainfall_7d REAL,
                rainfall_15d REAL,
                rainfall_30d REAL,
                awi_value REAL,
                forecast_rainfall REAL,
                data_completeness REAL NOT NULL,
                calculated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                risk_score REAL,
                risk_category TEXT NOT NULL,
                factor_scores TEXT NOT NULL,
                factor_weights TEXT NOT NULL,
                missing_factors TEXT NOT NULL,
                explanation TEXT NOT NULL,
                assessment_time TEXT NOT NULL,
                data_sources TEXT NOT NULL,
                completeness_score REAL NOT NULL,
                raw_payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gis_layers (
                layer_id TEXT PRIMARY KEY,
                layer_name TEXT NOT NULL,
                layer_type TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT NOT NULL,
                crs TEXT NOT NULL,
                geographic_coverage TEXT NOT NULL,
                resolution TEXT,
                last_updated TEXT NOT NULL,
                availability_status TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gis_features (
                feature_id TEXT PRIMARY KEY,
                layer_id TEXT NOT NULL,
                geometry_type TEXT NOT NULL,
                srid INTEGER NOT NULL DEFAULT 4326,
                min_lon REAL NOT NULL,
                min_lat REAL NOT NULL,
                max_lon REAL NOT NULL,
                max_lat REAL NOT NULL,
                geometry_json TEXT NOT NULL,
                properties_json TEXT NOT NULL,
                region_id TEXT,
                risk_category TEXT,
                feature_timestamp TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gis_features_layer ON gis_features(layer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gis_features_bbox ON gis_features(min_lon, max_lon, min_lat, max_lat)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                reporter_type TEXT NOT NULL,
                status TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                description TEXT,
                region_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emergency_resources (
                id TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                region_id TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_explanations (
                assessment_id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL,
                factor_contributions_json TEXT NOT NULL,
                increasing_factors_json TEXT NOT NULL,
                reducing_factors_json TEXT NOT NULL,
                unavailable_factors_json TEXT NOT NULL,
                explanation_text TEXT NOT NULL,
                data_reliability_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id TEXT PRIMARY KEY,
                user_role TEXT NOT NULL,
                user_id TEXT,
                location_context_json TEXT NOT NULL,
                messages_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        logger.info(f"Initialized SQLite database at {DB_PATH}")
    finally:
        conn.close()


def save_susceptibility_analysis(record: Dict[str, Any]) -> None:
    """Persist a Phase 2 susceptibility analysis record to SQLite."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO susceptibility_analyses (
                id, region_id, latitude, longitude, input_metadata,
                model_repository, model_revision, prediction_output,
                susceptibility_value, susceptibility_class, confidence,
                source_metadata, coverage_status, processing_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record.get("region_id"),
                record.get("latitude"),
                record.get("longitude"),
                json.dumps(record.get("input_metadata", {})),
                record["model_repository"],
                record["model_revision"],
                json.dumps(record.get("prediction_output", {})),
                record.get("susceptibility_value"),
                record.get("susceptibility_class"),
                record.get("confidence"),
                json.dumps(record.get("source_metadata", {})),
                record["coverage_status"],
                record["processing_time"],
                record["created_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_susceptibility_analysis_record(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a Phase 2 analysis record from SQLite by ID."""
    if not os.path.isfile(DB_PATH):
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM susceptibility_analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "region_id": row["region_id"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "input_metadata": json.loads(row["input_metadata"]),
            "model_repository": row["model_repository"],
            "model_revision": row["model_revision"],
            "prediction_output": json.loads(row["prediction_output"]),
            "susceptibility_value": row["susceptibility_value"],
            "susceptibility_class": row["susceptibility_class"],
            "confidence": row["confidence"],
            "source_metadata": json.loads(row["source_metadata"]),
            "coverage_status": row["coverage_status"],
            "processing_time": row["processing_time"],
            "created_at": row["created_at"],
        }
    finally:
        conn.close()


def save_weather_observation(obs: Dict[str, Any]) -> None:
    """Persist a deduplicated weather observation to SQLite."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO weather_observations (
                id, location_id, latitude, longitude, precipitation,
                temperature, humidity, wind_speed, weather_code,
                observation_time, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                obs["id"],
                obs["location_id"],
                obs["latitude"],
                obs["longitude"],
                obs.get("precipitation"),
                obs.get("temperature"),
                obs.get("humidity"),
                obs.get("wind_speed"),
                obs.get("weather_code"),
                obs["observation_time"],
                obs["source"],
                obs["created_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def save_rainfall_analysis(record: Dict[str, Any]) -> None:
    """Persist a Phase 3 rainfall analysis record to SQLite."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO rainfall_analyses (
                id, location_id, rainfall_1h, rainfall_3h, rainfall_6h,
                rainfall_24h, rainfall_72h, rainfall_7d, rainfall_15d,
                rainfall_30d, awi_value, forecast_rainfall,
                data_completeness, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["location_id"],
                record.get("rainfall_1h"),
                record.get("rainfall_3h"),
                record.get("rainfall_6h"),
                record.get("rainfall_24h"),
                record.get("rainfall_72h"),
                record.get("rainfall_7d"),
                record.get("rainfall_15d"),
                record.get("rainfall_30d"),
                record.get("awi_value"),
                record.get("forecast_rainfall"),
                record["data_completeness"],
                record["calculated_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def save_risk_assessment(record: Dict[str, Any]) -> None:
    """Persist a Phase 3 dynamic risk assessment to SQLite."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO risk_assessments (
                id, location_id, latitude, longitude, risk_score,
                risk_category, factor_scores, factor_weights, missing_factors,
                explanation, assessment_time, data_sources, completeness_score,
                raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["location_id"],
                record["latitude"],
                record["longitude"],
                record.get("risk_score"),
                record["risk_category"],
                json.dumps(record.get("factor_scores", {})),
                json.dumps(record.get("factor_weights", {})),
                json.dumps(record.get("missing_factors", [])),
                record["explanation"],
                record["assessment_time"],
                json.dumps(record.get("data_sources", [])),
                record["completeness_score"],
                json.dumps(record.get("raw_payload", {})),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_latest_risk_by_location(location_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the latest risk assessment for a location_id."""
    if not os.path.isfile(DB_PATH):
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT raw_payload FROM risk_assessments WHERE location_id = ? ORDER BY assessment_time DESC LIMIT 1",
            (location_id,),
        ).fetchone()
        return json.loads(row["raw_payload"]) if row else None
    finally:
        conn.close()


def get_risk_by_assessment_id(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific risk assessment by assessment_id."""
    if not os.path.isfile(DB_PATH):
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT raw_payload FROM risk_assessments WHERE id = ?",
            (assessment_id,),
        ).fetchone()
        return json.loads(row["raw_payload"]) if row else None
    finally:
        conn.close()


def get_risk_history_by_id_or_location(identifier: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve assessment history. If identifier matches an assessment_id, looks up its location_id
    and returns all historical assessments for that location. Otherwise queries by location_id directly.
    """
    if not os.path.isfile(DB_PATH):
        return []
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT location_id FROM risk_assessments WHERE id = ?",
            (identifier,),
        ).fetchone()
        loc_id = row["location_id"] if row else identifier
        rows = conn.execute(
            "SELECT raw_payload FROM risk_assessments WHERE location_id = ? ORDER BY assessment_time DESC LIMIT ?",
            (loc_id, limit),
        ).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]
    finally:
        conn.close()


def get_risk_hotspots(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve latest assessments per location where risk_category is HIGH or CRITICAL."""
    if not os.path.isfile(DB_PATH):
        return []
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT raw_payload FROM risk_assessments r1
            WHERE risk_category IN ('HIGH', 'CRITICAL')
              AND assessment_time = (
                  SELECT MAX(r2.assessment_time) FROM risk_assessments r2
                  WHERE r2.location_id = r1.location_id
              )
            ORDER BY risk_score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]
    finally:
        conn.close()


def save_risk_explanation(record: Dict[str, Any]) -> None:
    """Persist structured Phase 5 XAI explanation for an assessment."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO risk_explanations (
                assessment_id, location_id, factor_contributions_json,
                increasing_factors_json, reducing_factors_json,
                unavailable_factors_json, explanation_text,
                data_reliability_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["assessment_id"],
                record["location_id"],
                json.dumps(record["factor_contributions"]),
                json.dumps(record["increasing_factors"]),
                json.dumps(record["reducing_factors"]),
                json.dumps(record["unavailable_factors"]),
                record["explanation_text"],
                json.dumps(record["data_reliability"]),
                record["created_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_risk_assessments_chronological(
    location_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Retrieve stored risk assessments for a location in chronological (ASC) order."""
    if not os.path.isfile(DB_PATH):
        return []
    conn = get_db_connection()
    try:
        # Support passing either location_id or an assessment_id
        row = conn.execute(
            "SELECT location_id FROM risk_assessments WHERE id = ?",
            (location_id,),
        ).fetchone()
        loc_id = row["location_id"] if row else location_id

        clauses = ["location_id = ?"]
        params: List[Any] = [loc_id]
        if start_date:
            clauses.append("assessment_time >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("assessment_time <= ?")
            params.append(end_date)
        params.append(limit)

        sql = (
            f"SELECT raw_payload FROM risk_assessments WHERE {' AND '.join(clauses)} "
            "ORDER BY assessment_time ASC LIMIT ?"
        )
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]
    finally:
        conn.close()


def create_agent_session(session: Dict[str, Any]) -> None:
    """Create a new Phase 6 agent conversation session."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO agent_sessions (
                session_id, user_role, user_id, location_context_json,
                messages_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["session_id"],
                session["user_role"],
                session.get("user_id"),
                json.dumps(session.get("location_context", {})),
                json.dumps(session.get("messages", [])),
                session["created_at"],
                session["updated_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_agent_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a Phase 6 agent session by ID."""
    if not os.path.isfile(DB_PATH):
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM agent_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "user_role": row["user_role"],
            "user_id": row["user_id"],
            "location_context": json.loads(row["location_context_json"]),
            "messages": json.loads(row["messages_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def update_agent_session(
    session_id: str,
    location_context: Dict[str, Any],
    messages: List[Dict[str, Any]],
    updated_at: str,
) -> None:
    """Update conversation history and location context for an existing session."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE agent_sessions
            SET location_context_json = ?, messages_json = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (json.dumps(location_context), json.dumps(messages), updated_at, session_id),
        )
        conn.commit()
    finally:
        conn.close()
