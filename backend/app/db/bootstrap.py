import sqlite3
from pathlib import Path

import duckdb

from app.core.config import settings
from app.db.analytics import initialize_analytics_schema


def initialize_sqlite(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT OR REPLACE INTO app_metadata(key, value)
            VALUES ('schema_version', 'phase1')
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS esco_occupations (
                concept_uri TEXT PRIMARY KEY,
                preferred_label TEXT NOT NULL,
                code TEXT,
                isco_group TEXT,
                dataset_version TEXT NOT NULL,
                source_mode TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS esco_skills (
                concept_uri TEXT PRIMARY KEY,
                preferred_label TEXT NOT NULL,
                alternative_labels_json TEXT NOT NULL DEFAULT '[]',
                is_language_skill INTEGER NOT NULL DEFAULT 0,
                dataset_version TEXT NOT NULL,
                source_mode TEXT NOT NULL
            )
            """
        )
        esco_skill_columns = {
            row[1]
            for row in con.execute("PRAGMA table_info('esco_skills')").fetchall()
        }
        if "is_language_skill" not in esco_skill_columns:
            con.execute(
                "ALTER TABLE esco_skills ADD COLUMN is_language_skill INTEGER NOT NULL DEFAULT 0"
            )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS esco_occupation_skills (
                occupation_uri TEXT NOT NULL,
                skill_uri TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                dataset_version TEXT NOT NULL,
                source_mode TEXT NOT NULL,
                PRIMARY KEY (occupation_uri, skill_uri, relation_type)
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ttv_calibration_cases (
                case_id TEXT PRIMARY KEY,
                country_iso3 TEXT NOT NULL,
                employment_mode TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                composition TEXT NOT NULL,
                candidate_weeks_min REAL NOT NULL,
                candidate_weeks_max REAL NOT NULL,
                observed_weeks REAL NOT NULL,
                source_label TEXT,
                observed_at TEXT,
                sample_role TEXT NOT NULL DEFAULT 'development',
                start_event_definition_version TEXT,
                viability_outcome_definition_version TEXT,
                calibration_protocol_version TEXT,
                stage_timings_json TEXT NOT NULL DEFAULT '{}',
                context_json TEXT NOT NULL DEFAULT '{}',
                imported_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ttv_calibration_observations (
                case_id TEXT PRIMARY KEY,
                country_iso3 TEXT NOT NULL,
                status TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                composition TEXT NOT NULL,
                candidate_weeks_min REAL NOT NULL,
                candidate_weeks_max REAL NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                baseline_json TEXT NOT NULL DEFAULT '{}',
                completion_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ttv_calibration_columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info('ttv_calibration_cases')"
            ).fetchall()
        }
        if "stage_timings_json" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN stage_timings_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "context_json" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN context_json TEXT NOT NULL DEFAULT '{}'"
            )

        if "sample_role" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN sample_role TEXT NOT NULL DEFAULT 'development'"
            )
        if "start_event_definition_version" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN start_event_definition_version TEXT"
            )
        if "viability_outcome_definition_version" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN viability_outcome_definition_version TEXT"
            )
        if "calibration_protocol_version" not in ttv_calibration_columns:
            con.execute(
                "ALTER TABLE ttv_calibration_cases "
                "ADD COLUMN calibration_protocol_version TEXT"
            )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS personal_profile (
                profile_id TEXT PRIMARY KEY,
                age INTEGER,
                current_country TEXT,
                citizenships_json TEXT NOT NULL DEFAULT '[]',
                profession TEXT,
                skills_json TEXT NOT NULL DEFAULT '[]',
                languages_json TEXT NOT NULL DEFAULT '[]',
                household_size INTEGER NOT NULL DEFAULT 1,
                monthly_net_income REAL,
                liquid_savings REAL,
                remote_work INTEGER NOT NULL DEFAULT 0,
                preferences_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT OR IGNORE INTO app_metadata(key, value)
            VALUES ('esco_dataset_mode', 'none')
            """
        )
        con.execute(
            """
            INSERT OR IGNORE INTO app_metadata(key, value)
            VALUES ('esco_dataset_version', 'none')
            """
        )
        con.commit()
    finally:
        con.close()


def initialize_duckdb(path: Path) -> None:
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_metadata (
                key VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT OR REPLACE INTO analytics_metadata
            VALUES ('schema_version', 'phase1')
            """
        )
    finally:
        con.close()


def initialize_datastores() -> None:
    initialize_sqlite(settings.sqlite_path)
    initialize_duckdb(settings.duckdb_path)
    initialize_analytics_schema()

    from app.esco_store import esco_status, seed_esco_partial

    if esco_status()["mode"] == "none":
        seed_esco_partial()


def datastore_status() -> dict[str, bool]:
    result = {"sqlite": False, "duckdb": False}

    try:
        con = sqlite3.connect(settings.sqlite_path)
        try:
            value = con.execute(
                "SELECT value FROM app_metadata WHERE key='schema_version'"
            ).fetchone()
            result["sqlite"] = value is not None
        finally:
            con.close()
    except Exception:
        pass

    try:
        con = duckdb.connect(str(settings.duckdb_path), read_only=True)
        try:
            metadata_ok = con.execute(
                "SELECT value FROM analytics_metadata WHERE key='schema_version'"
            ).fetchone()
            schema_ok = con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name IN ('countries', 'sources', 'indicators', 'observations')
                """
            ).fetchone()[0]
            result["duckdb"] = metadata_ok is not None and schema_ok == 4
        finally:
            con.close()
    except Exception:
        pass

    return result
