from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


DATASET_ID = "CEDEFOP_OJA_IMBALANCE"
SOURCE_ID = "CEDEFOP"
RELEASE_VERSION = "2026-05"
DOI = "10.2906/752555516245105"
CANONICAL_URL = "https://www.cedefop.europa.eu/en/datasets/oja-imbalance-occupations"
PUBLISHED_FILENAME = "cedefop-oja-imbalance-2026-05.csv"


ALIASES = {
    "occupation_code": {
        "isco",
        "isco code",
        "isco08",
        "isco 08",
        "isco 4",
        "isco_4",
        "occupation code",
        "oc code",
        "code",
    },
    "major_group": {
        "isco 1",
        "isco_1",
        "isco 1 digit",
        "major group",
    },
    "occupation_label": {
        "occupation",
        "occupation label",
        "occupation name",
        "label",
    },
    "score": {
        "score",
        "shortage score",
        "imbalance score",
        "normalised score",
        "normalized score",
    },
    "country": {
        "country",
        "country code",
        "geo",
        "geography",
    },
}


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def read_preview(path: Path, max_rows: int = 20) -> tuple[list[str], list[list[str]], str]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    dialect = _dialect(raw[:8192])
    rows = list(csv.reader(raw.splitlines(), dialect))
    if not rows:
        return [], [], getattr(dialect, "delimiter", ",")
    return rows[0], rows[1:max_rows + 1], getattr(dialect, "delimiter", ",")


def detect_schema(headers: list[str]) -> dict:
    normalised = [_norm(value) for value in headers]
    matches: dict[str, int] = {}

    for field, aliases in ALIASES.items():
        for index, header in enumerate(normalised):
            if header in aliases:
                matches[field] = index
                break

    core = "occupation_code" in matches and "score" in matches
    if core:
        status = "recognised"
    elif matches:
        status = "partial"
    else:
        status = "unrecognised"

    return {
        "status": status,
        "headers": headers,
        "matches": matches,
        "ready_for_parser_implementation": core,
    }


def inspect_csv(path: Path, max_rows: int = 20) -> dict:
    headers, sample_rows, delimiter = read_preview(path, max_rows=max_rows)
    schema = detect_schema(headers)
    return {
        "dataset_id": DATASET_ID,
        "source_id": SOURCE_ID,
        "release_version": RELEASE_VERSION,
        "doi": DOI,
        "canonical_url": CANONICAL_URL,
        "published_filename": PUBLISHED_FILENAME,
        "file": str(path),
        "delimiter": delimiter,
        **schema,
        "sample_rows": sample_rows[:5],
        "geographic_scope": "EU27",
        "notes": [
            "This inspector does not write OJA imbalance data to DuckDB.",
            "The published Cedefop score is exploratory and must remain context-only.",
            "The released CSV contains one EU27-level score per ISCO-4 occupation; it is not country-specific evidence.",
            "AUGUR will not infer skill-demand shares, employer counts or hiring probabilities from this dataset.",
        ],
    }


def parse_csv(path: Path) -> list[dict]:
    headers, rows, _delimiter = read_preview(path, max_rows=1000000)
    schema = detect_schema(headers)
    if not schema["ready_for_parser_implementation"]:
        raise ValueError("Cedefop OJA imbalance CSV schema is not recognised.")

    matches = schema["matches"]
    code_index = matches["occupation_code"]
    label_index = matches["occupation_label"]
    score_index = matches["score"]
    major_index = matches.get("major_group")
    retrieved_at = datetime.now(timezone.utc)

    parsed = []
    for row in rows:
        if max(code_index, label_index, score_index) >= len(row):
            continue

        code = str(row[code_index] or "").strip()
        label = str(row[label_index] or "").strip()
        raw_score = str(row[score_index] or "").strip()
        if not code or not label or not raw_score:
            continue
        if len(code) != 4 or not code.isdigit():
            continue

        try:
            score = float(raw_score)
        except ValueError:
            continue

        if not 0.0 <= score <= 1.0:
            continue

        major_group_label = None
        if major_index is not None and major_index < len(row):
            major_group_label = str(row[major_index] or "").strip() or None

        parsed.append({
            "isco08": code,
            "major_group_label": major_group_label,
            "occupation_label": label,
            "score": score,
            "source_id": SOURCE_ID,
            "dataset_id": DATASET_ID,
            "release_version": RELEASE_VERSION,
            "retrieved_at": retrieved_at,
            "source_updated_at": RELEASE_VERSION,
        })

    return parsed
