"""Fail-closed Eurostat NUTS2 regional contracts, independent of country choice."""
from __future__ import annotations

from app.services.global_evidence_contract import EvidenceContract, validate_observation
from app.ingestion.eurostat_regional_labour import REGIONAL_LABOUR_SERIES
from app.ingestion.eurostat_regional_housing import REGIONAL_HOUSING_SERIES

CONTRACTS = {
    cfg["indicator_id"]: (cfg["dataset_id"], cfg["unit"])
    for cfg in REGIONAL_LABOUR_SERIES + REGIONAL_HOUSING_SERIES
}


def validate_eurostat_regional_rows(rows: list[dict], *, allowed_indicators: set[str]) -> None:
    """Raise before writing if source, dimension, unit or geography is wrong."""
    if not allowed_indicators or not allowed_indicators <= CONTRACTS.keys():
        raise ValueError("Unknown Eurostat regional indicator allowlist")
    for row in rows:
        indicator = row.get("indicator_id")
        if indicator not in allowed_indicators:
            raise ValueError(f"Unexpected Eurostat regional indicator: {indicator}")
        dataset, unit = CONTRACTS[indicator]
        normalized = dict(row)
        normalized["geo_level"] = str(row.get("geo_level") or "").lower()
        errors = validate_observation(
            EvidenceContract(indicator, unit, ("nuts2",), "EUROSTAT", dataset),
            normalized,
        )
        code = str(row.get("geo_code") or "")
        if len(code) != 4 or not code[:2].isalpha() or not code[2:].isalnum():
            errors.append("nuts2_code_invalid")
        if errors:
            raise ValueError(f"Eurostat regional contract failed for {code}: {', '.join(errors)}")
