from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Iterable

from app.core.config import settings


ESCO_VERSION = "1.2.1"

# Minimal official seed used only to validate the local matching pipeline.
# It is deliberately marked as partial and must never unlock TTV by itself.
SEED_OCCUPATIONS = [
    {
        "concept_uri": "urn:augur:esco-seed:ict-system-administrator",
        "preferred_label": "ICT system administrator",
        "code": None,
        "isco_group": "2522",
    },
    {
        "concept_uri": "urn:augur:esco-seed:ict-network-engineer",
        "preferred_label": "ICT network engineer",
        "code": None,
        "isco_group": "2523",
    },
]

SEED_SKILLS = [
    {
        "concept_uri": "http://data.europa.eu/esco/skill/acf0a78c-f4e3-4bd9-a5cc-9cf4791b3b95",
        "preferred_label": "implement a virtual private network",
        "alternative_labels": [
            "installing a virtual private network",
            "VPN implementing",
            "VPN installing",
            "implement a VPN",
            "install a VPN",
        ],
    },
    {
        "concept_uri": "http://data.europa.eu/esco/skill/1e7ed56a-6d6b-422f-962e-38543d150755",
        "preferred_label": "manage changes in ICT system",
        "alternative_labels": [
            "ICT system upgrade",
        ],
    },
    {
        "concept_uri": "http://data.europa.eu/esco/skill/69cfc5ed-6569-4aca-a4cc-fd782ba51d9c",
        "preferred_label": "implement ICT risk management",
        "alternative_labels": [],
    },
]

SEED_RELATIONS = [
    {
        "occupation_uri": "urn:augur:esco-seed:ict-system-administrator",
        "skill_uri": "http://data.europa.eu/esco/skill/acf0a78c-f4e3-4bd9-a5cc-9cf4791b3b95",
        "relation_type": "essential",
    },
    {
        "occupation_uri": "urn:augur:esco-seed:ict-network-engineer",
        "skill_uri": "http://data.europa.eu/esco/skill/acf0a78c-f4e3-4bd9-a5cc-9cf4791b3b95",
        "relation_type": "essential",
    },
    {
        "occupation_uri": "urn:augur:esco-seed:ict-system-administrator",
        "skill_uri": "http://data.europa.eu/esco/skill/1e7ed56a-6d6b-422f-962e-38543d150755",
        "relation_type": "essential",
    },
    {
        "occupation_uri": "urn:augur:esco-seed:ict-system-administrator",
        "skill_uri": "http://data.europa.eu/esco/skill/69cfc5ed-6569-4aca-a4cc-fd782ba51d9c",
        "relation_type": "optional",
    },
]


def _connect():
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row
    return con


def seed_esco_partial() -> dict:
    con = _connect()
    try:
        for item in SEED_OCCUPATIONS:
            con.execute(
                """
                INSERT OR REPLACE INTO esco_occupations (
                    concept_uri, preferred_label, code, isco_group,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, ?, 'seed')
                """,
                [
                    item["concept_uri"],
                    item["preferred_label"],
                    item["code"],
                    item["isco_group"],
                    ESCO_VERSION,
                ],
            )

        for item in SEED_SKILLS:
            con.execute(
                """
                INSERT OR REPLACE INTO esco_skills (
                    concept_uri, preferred_label, alternative_labels_json,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, 'seed')
                """,
                [
                    item["concept_uri"],
                    item["preferred_label"],
                    json.dumps(item["alternative_labels"]),
                    ESCO_VERSION,
                ],
            )

        for item in SEED_RELATIONS:
            con.execute(
                """
                INSERT OR REPLACE INTO esco_occupation_skills (
                    occupation_uri, skill_uri, relation_type,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, 'seed')
                """,
                [
                    item["occupation_uri"],
                    item["skill_uri"],
                    item["relation_type"],
                    ESCO_VERSION,
                ],
            )

        con.execute(
            "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('esco_dataset_mode', 'seed')"
        )
        con.execute(
            "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('esco_dataset_version', ?)",
            [ESCO_VERSION],
        )
        con.commit()
    finally:
        con.close()

    return esco_status()


def esco_status() -> dict:
    con = _connect()
    try:
        metadata = dict(
            con.execute(
                "SELECT key, value FROM app_metadata WHERE key IN ('esco_dataset_mode', 'esco_dataset_version')"
            ).fetchall()
        )
        occupations = con.execute("SELECT COUNT(*) FROM esco_occupations").fetchone()[0]
        skills = con.execute("SELECT COUNT(*) FROM esco_skills").fetchone()[0]
        relations = con.execute("SELECT COUNT(*) FROM esco_occupation_skills").fetchone()[0]
    finally:
        con.close()

    return {
        "mode": metadata.get("esco_dataset_mode", "none"),
        "version": metadata.get("esco_dataset_version", "none"),
        "occupation_count": occupations,
        "skill_count": skills,
        "relation_count": relations,
    }


def _find_csv(root: Path, needle: str) -> Path:
    candidates = [
        path
        for path in root.rglob("*.csv")
        if needle.lower() in path.stem.lower()
    ]
    if not candidates:
        raise FileNotFoundError(f"ESCO CSV not found: {needle}")
    return sorted(candidates, key=lambda value: len(str(value)))[0]


def _first(row: dict[str, str], names: Iterable[str]) -> str | None:
    lowered = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ""):
            return value
    return None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def import_esco_csv_package(root: Path, version: str = ESCO_VERSION) -> dict:
    occupations_file = _find_csv(root, "occupations")
    skills_file = _find_csv(root, "skills")
    relations_file = _find_csv(root, "occupationSkillRelations")

    occupation_rows = _read_csv(occupations_file)
    skill_rows = _read_csv(skills_file)
    relation_rows = _read_csv(relations_file)

    con = _connect()
    try:
        con.execute("DELETE FROM esco_occupation_skills")
        con.execute("DELETE FROM esco_skills")
        con.execute("DELETE FROM esco_occupations")

        for row in occupation_rows:
            uri = _first(row, ["conceptUri", "concept_uri", "uri"])
            label = _first(row, ["preferredLabel", "preferred_label", "title"])
            if not uri or not label:
                continue

            code = _first(row, ["code", "escoCode", "esco_code"])
            isco = _first(row, ["iscoGroup", "isco_group", "iscoCode", "isco_code"])

            con.execute(
                """
                INSERT OR REPLACE INTO esco_occupations (
                    concept_uri, preferred_label, code, isco_group,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, ?, 'full')
                """,
                [uri, label, code, isco, version],
            )

        for row in skill_rows:
            uri = _first(row, ["conceptUri", "concept_uri", "uri"])
            label = _first(row, ["preferredLabel", "preferred_label", "title"])
            if not uri or not label:
                continue

            alt = _first(
                row,
                [
                    "altLabels",
                    "alternativeLabels",
                    "alternative_labels",
                    "alt_labels",
                ],
            )
            alternatives = [
                value.strip()
                for value in (alt or "").replace("|", "\n").splitlines()
                if value.strip()
            ]

            con.execute(
                """
                INSERT OR REPLACE INTO esco_skills (
                    concept_uri, preferred_label, alternative_labels_json,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, 'full')
                """,
                [uri, label, json.dumps(alternatives), version],
            )

        for row in relation_rows:
            occupation_uri = _first(
                row,
                [
                    "occupationUri",
                    "occupation_uri",
                    "occupationConceptUri",
                    "occupation_concept_uri",
                ],
            )
            skill_uri = _first(
                row,
                [
                    "skillUri",
                    "skill_uri",
                    "skillConceptUri",
                    "skill_concept_uri",
                ],
            )
            relation_type = _first(
                row,
                ["relationType", "relation_type", "type"],
            ) or "related"

            if not occupation_uri or not skill_uri:
                continue

            con.execute(
                """
                INSERT OR REPLACE INTO esco_occupation_skills (
                    occupation_uri, skill_uri, relation_type,
                    dataset_version, source_mode
                )
                VALUES (?, ?, ?, ?, 'full')
                """,
                [occupation_uri, skill_uri, relation_type.lower(), version],
            )

        con.execute(
            "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('esco_dataset_mode', 'full')"
        )
        con.execute(
            "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('esco_dataset_version', ?)",
            [version],
        )
        con.commit()
    finally:
        con.close()

    return {
        **esco_status(),
        "files": {
            "occupations": str(occupations_file),
            "skills": str(skills_file),
            "relations": str(relations_file),
        },
    }


def occupation_skill_rows(occupation_label: str) -> list[dict]:
    con = _connect()
    try:
        result = con.execute(
            """
            SELECT
                o.concept_uri AS occupation_uri,
                o.preferred_label AS occupation_label,
                s.concept_uri AS skill_uri,
                s.preferred_label AS skill_label,
                s.alternative_labels_json,
                r.relation_type,
                r.source_mode
            FROM esco_occupations o
            JOIN esco_occupation_skills r
              ON r.occupation_uri = o.concept_uri
            JOIN esco_skills s
              ON s.concept_uri = r.skill_uri
            WHERE LOWER(o.preferred_label) = LOWER(?)
            ORDER BY
                CASE WHEN r.relation_type = 'essential' THEN 0 ELSE 1 END,
                s.preferred_label
            """,
            [occupation_label],
        )
        rows = []
        for row in result.fetchall():
            item = dict(row)
            item["alternative_labels"] = json.loads(
                item.pop("alternative_labels_json") or "[]"
            )
            rows.append(item)
        return rows
    finally:
        con.close()
