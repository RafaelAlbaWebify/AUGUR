import pytest

from scripts.audit_legacy_nuts_vintage import classify_claims, extract_codes


def test_extract_codes_rejects_wrong_level():
    payload = {
        "type": "FeatureCollection",
        "features": [{"properties": {"NUTS_ID": "ES12", "LEVL_CODE": 2}}],
    }
    assert extract_codes(payload, "nuts2") == {"ES12"}
    with pytest.raises(ValueError, match="Unexpected GISCO level"):
        extract_codes(payload, "nuts3")


def test_audit_distinguishes_impossible_current_claims_from_ambiguous_vintage():
    official = {
        "nuts2": {"ES12", "IE05"},
        "nuts3": {"ES120"},
    }
    observations = [
        {
            "geo_level": "nuts2",
            "geo_code": "ES12",
            "source_id": "EUROSTAT",
            "dataset_id": "lfst_r_lfe2emprt",
            "first_period": 2018,
            "last_period": 2025,
            "observation_count": 8,
        },
        {
            "geo_level": "nuts2",
            "geo_code": "IE01",
            "source_id": "EUROSTAT",
            "dataset_id": "lfst_r_lfe2emprt",
            "first_period": 2018,
            "last_period": 2020,
            "observation_count": 3,
        },
    ]
    registry = [
        {
            "geo_id": "NUTS_2024:ES12",
            "geo_level": "nuts2",
            "source_geo_code": "ES12",
        },
        {
            "geo_id": "NUTS_2024:IE01",
            "geo_level": "nuts2",
            "source_geo_code": "IE01",
        },
    ]

    report = classify_claims(official, observations, registry)

    assert report["mutation_performed"] is False
    assert report["summary"] == {
        "nuts2024_observation_groups": 2,
        "definite_observation_mislabels": 1,
        "current_code_vintage_unverified": 1,
        "nuts2024_registry_rows": 2,
        "invalid_current_registry_rows": 1,
    }
    assert report["definite_observation_mislabels"][0]["geo_code"] == "IE01"
    assert (
        report["current_code_vintage_unverified"][0]["audit_status"]
        == "code_current_observation_vintage_unverified"
    )
    assert report["invalid_current_registry_rows"][0]["source_geo_code"] == "IE01"


def test_current_code_membership_never_certifies_observation_vintage():
    report = classify_claims(
        {"nuts2": {"PT11"}, "nuts3": set()},
        [{"geo_level": "nuts2", "geo_code": "PT11"}],
        [],
    )
    row = report["current_code_vintage_unverified"][0]
    assert row["audit_status"] == "code_current_observation_vintage_unverified"
