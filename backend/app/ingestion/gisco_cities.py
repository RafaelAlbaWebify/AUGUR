from __future__ import annotations

import re
import unicodedata
from collections import defaultdict


CITY_CODE_RE = re.compile(r"^[A-Z]{2}\d{3}C$")


def normalize_city_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def city_code(feature: dict) -> str | None:
    properties = feature.get("properties") or {}
    candidates = [
        properties.get("URAU_CODE"),
        properties.get("URAU_ID"),
        properties.get("CITY_CODE"),
        properties.get("CODE"),
        feature.get("id"),
        *properties.values(),
    ]
    for value in candidates:
        if not isinstance(value, str):
            continue
        code = value.upper()
        if CITY_CODE_RE.fullmatch(code):
            return code
    return None


def city_name(feature: dict) -> str | None:
    properties = feature.get("properties") or {}
    for key in (
        "NAME_LATN",
        "URAU_NAME",
        "CITY_NAME",
        "NAME",
        "LABEL",
    ):
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def gisco_city_catalog(payload: dict, country_codes: set[str] | None = None) -> list[dict]:
    rows = []
    for feature in payload.get("features", []):
        code = city_code(feature)
        name = city_name(feature)
        if not code or not name:
            continue
        country = code[:2]
        if country_codes and country not in country_codes:
            continue
        rows.append({
            "city_code": code,
            "country_code": country,
            "city_name": name,
            "normalized_name": normalize_city_name(name),
        })
    return rows


def match_eea_cities_to_gisco(
    gisco_rows: list[dict],
    eea_rows: list[dict],
) -> dict:
    candidates: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in gisco_rows:
        candidates[
            (row["country_code"], row["normalized_name"])
        ].append(row)

    matched = []
    unmatched = []
    ambiguous = []

    for eea in eea_rows:
        country = str(eea.get("countryCode") or "").upper()
        name = str(eea.get("cityName") or "").strip()
        key = (country, normalize_city_name(name))
        options = candidates.get(key, [])

        if len(options) == 1:
            target = options[0]
            matched.append({
                "country_code": country,
                "eea_city_name": name,
                "city_code": target["city_code"],
                "gisco_city_name": target["city_name"],
                "match_method": "normalized_exact",
            })
        elif len(options) > 1:
            ambiguous.append({
                "country_code": country,
                "eea_city_name": name,
                "candidate_codes": sorted(
                    option["city_code"] for option in options
                ),
            })
        else:
            unmatched.append({
                "country_code": country,
                "eea_city_name": name,
            })

    return {
        "matched": matched,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "ambiguous_count": len(ambiguous),
    }
