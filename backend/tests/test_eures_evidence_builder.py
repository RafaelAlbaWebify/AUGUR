from __future__ import annotations

import json

import pytest

from app.services import eures_evidence_builder as module


def _candidate(
    label: str,
    isco: str,
    score: float,
    method: str = "token_overlap",
):
    return {
        "preferred_label": label,
        "isco_group": isco,
        "code": isco,
        "match_score": score,
        "match_method": method,
    }


def test_exact_esco_match_resolves_unit_group():
    result = module.resolve_eures_occupation(
        "Systems analysts",
        search=lambda query, limit: [
            _candidate(
                "Systems analysts",
                "2511",
                1.0,
                "exact_label",
            )
        ],
    )

    assert result["status"] == "resolved"
    assert result["isco_unit"] == "2511"
    assert result["match_score"] == 1.0


def test_ambiguous_esco_match_is_not_guessed():
    result = module.resolve_eures_occupation(
        "Network specialist",
        search=lambda query, limit: [
            _candidate(
                "Computer network professionals",
                "2523",
                0.88,
            ),
            _candidate(
                "Computer network and systems technicians",
                "3513",
                0.84,
            ),
        ],
        threshold=0.84,
        min_margin=0.08,
    )

    assert result["status"] == "unresolved"
    assert result["reason"] == "ambiguous_esco_match"
    assert result["margin"] == 0.04


def test_low_confidence_esco_match_is_not_accepted():
    result = module.resolve_eures_occupation(
        "Specialist role",
        search=lambda query, limit: [
            _candidate(
                "Systems analysts",
                "2511",
                0.61,
            )
        ],
        threshold=0.84,
    )

    assert result["status"] == "unresolved"
    assert result["reason"] == "match_below_threshold"


def test_builder_keeps_resolved_and_unresolved_rows_separate():
    mapping = {
        "Systems analysts": [
            _candidate(
                "Systems analysts",
                "2511",
                1.0,
                "exact_label",
            )
        ],
        "Unknown occupation": [],
    }

    result = module.build_eures_unit_group_evidence(
        [
            {
                "occupation_label": "Systems analysts",
                "shortage_countries": "IE, RO",
                "surplus_countries": "PT",
            },
            {
                "occupation_label": "Unknown occupation",
                "shortage_countries": "ES",
                "surplus_countries": "",
            },
        ],
        source_metadata={
            "evidence_id": "test",
            "rule_version": "test-v1",
            "report_year": 2026,
            "conditions_year": 2025,
        },
        search=lambda query, limit: mapping.get(query, []),
    )

    assert result["resolved_count"] == 1
    assert result["unresolved_count"] == 1
    assert result["ready_for_review"] is False
    assert result["unit_group_signals"]["2511"] == {
        "occupation_label": "Systems analysts",
        "esco_label": "Systems analysts",
        "match_score": 1.0,
        "match_method": "exact_label",
        "shortage_countries": ["IE", "RO"],
        "surplus_countries": ["PT"],
    }
    assert result["unresolved"][0]["reason"] == "no_esco_candidate"


def test_duplicate_isco_unit_requires_review():
    result = module.build_eures_unit_group_evidence(
        [
            {
                "occupation_label": "Label one",
                "shortage_countries": "IE",
                "surplus_countries": "",
            },
            {
                "occupation_label": "Label two",
                "shortage_countries": "PT",
                "surplus_countries": "",
            },
        ],
        source_metadata={"evidence_id": "test"},
        search=lambda query, limit: [
            _candidate(
                query,
                "2511",
                1.0,
                "exact_label",
            )
        ],
    )

    assert result["resolved_count"] == 1
    assert result["unresolved_count"] == 1
    assert result["unresolved"][0]["reason"] == "duplicate_isco_unit"
    assert result["ready_for_review"] is False


def test_invalid_country_code_is_not_silently_kept():
    result = module.build_eures_unit_group_evidence(
        [
            {
                "occupation_label": "Systems analysts",
                "shortage_countries": "IRL",
                "surplus_countries": "",
            }
        ],
        source_metadata={"evidence_id": "test"},
        search=lambda query, limit: [
            _candidate(
                "Systems analysts",
                "2511",
                1.0,
                "exact_label",
            )
        ],
    )

    assert result["resolved_count"] == 0
    assert result["unresolved_count"] == 1
    assert result["unresolved"][0]["reason"] == "invalid_country_codes"


def test_csv_builder_requires_full_esco(monkeypatch, tmp_path):
    path = tmp_path / "eures.csv"
    path.write_text(
        "occupation_label,shortage_countries,surplus_countries\n"
        "Systems analysts,IE,PT\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "seed",
            "version": "1.2.1",
        },
    )

    with pytest.raises(RuntimeError, match="Full ESCO is required"):
        module.build_eures_unit_group_evidence_from_csv(
            path,
            source_metadata={"evidence_id": "test"},
        )


def test_review_artifact_is_written_without_mutating_manifest(tmp_path):
    result = {
        "builder_version": "test",
        "resolved_count": 1,
        "unresolved_count": 0,
        "unit_group_signals": {
            "2511": {
                "occupation_label": "Systems analysts",
            }
        },
        "unresolved": [],
        "ready_for_review": True,
    }
    output = tmp_path / "review.json"

    saved = module.write_eures_review_artifact(
        result,
        output,
    )

    assert saved == output.resolve()
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_csv_builder_parses_normalized_table_with_full_esco(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "eures.csv"
    path.write_text(
        "occupation_label,shortage_countries,surplus_countries\n"
        "Systems analysts,\"IE RO\",PT\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
        },
    )

    result = module.build_eures_unit_group_evidence_from_csv(
        path,
        source_metadata={
            "evidence_id": "test-annex",
            "rule_version": "test-v1",
            "report_year": 2026,
            "conditions_year": 2025,
        },
        search=lambda query, limit: [
            _candidate(
                "Systems analysts",
                "2511",
                1.0,
                "exact_label",
            )
        ],
    )

    assert result["resolved_count"] == 1
    assert result["unresolved_count"] == 0
    assert result["ready_for_review"] is True
    assert result["esco_version"] == "1.2.1"
    assert result["unit_group_signals"]["2511"]["shortage_countries"] == [
        "IE",
        "RO",
    ]
