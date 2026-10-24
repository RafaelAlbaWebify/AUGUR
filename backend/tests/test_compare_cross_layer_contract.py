"""Cross-layer comparison contract and controlled mutation detection."""
from copy import deepcopy
from pathlib import Path

from scripts.check_compare_contract import fixture_response, verify_compare_shape, TS_FILE


def test_current_compare_response_matches_frontend_types():
    assert verify_compare_shape(fixture_response(), TS_FILE.read_text(encoding="utf-8")) == []


def test_deleted_backend_field_is_detected():
    response = deepcopy(fixture_response())
    del response["indicators"][0]["countries"]["ESP"]["period"]
    issues = verify_compare_shape(response, TS_FILE.read_text(encoding="utf-8"))
    assert any("countries[ESP].period is missing" in issue for issue in issues)


def test_renamed_frontend_field_is_detected():
    source = TS_FILE.read_text(encoding="utf-8")
    changed = source.replace("  source_id: string", "  provider_identity: string", 1)
    assert changed != source
    issues = verify_compare_shape(fixture_response(), changed)
    assert any("ComparisonCountryValue missing required fields" in issue for issue in issues)
