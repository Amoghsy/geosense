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
