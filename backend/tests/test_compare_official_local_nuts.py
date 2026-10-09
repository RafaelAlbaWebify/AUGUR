import pytest
from scripts.compare_official_local_nuts import compare_catalogs


def test_code_membership_not_confused_with_statistical_coverage():
    official = {
        "scope": "official_gisco_nuts_2024_catalog_only",
        "catalogs": {
            level: {
                iso2: {"codes": (["ES11", "ES12"] if level == "nuts2" and iso2 == "ES" else [iso2 + ("01" if level == "nuts2" else "011")]), "count": (2 if level == "nuts2" and iso2 == "ES" else 1)}
                for iso2 in ("ES", "IE", "PT")
            }
            for level in ("nuts2", "nuts3")
        },
    }
    local = {
        "status": "observed_local_registry_only",
        "items": [
            {"country_iso3": "ESP", "geo_level": "nuts2",
             "geography_system": "NUTS_2024", "source_geo_code": "ES11",
             "has_evidence": False},
            {"country_iso3": "ESP", "geo_level": "nuts2",
             "geography_system": "NUTS_2024", "source_geo_code": "ES99",
             "has_evidence": True},
        ],
    }
    report = compare_catalogs(official, local)
    row = report["results"][0]
    assert row["matching_codes"] == ["ES11"]
    assert row["official_codes_not_registered"] == ["ES12"]
    assert row["registered_codes_not_in_official_catalog"] == ["ES99"]
    assert row["matching_codes_without_observations"] == ["ES11"]
    assert len(report["results"]) == 6


def test_missing_official_country_is_rejected():
    official = {"scope": "official_gisco_nuts_2024_catalog_only",
                "catalogs": {"nuts2": {}, "nuts3": {}}}
    local = {"status": "observed_local_registry_only", "items": []}
    with pytest.raises(ValueError, match="Missing official catalog"):
        compare_catalogs(official, local)


def test_duplicate_local_code_is_rejected():
    official = {"scope": "official_gisco_nuts_2024_catalog_only",
                "catalogs": {level: {code: {"codes": [code+"11"], "count": 1}
                            for code in ("ES", "IE", "PT")}
                             for level in ("nuts2", "nuts3")}}
    entry = {"country_iso3": "ESP", "geo_level": "nuts2",
             "geography_system": "NUTS_2024", "source_geo_code": "ES11",
             "has_evidence": True}
    local = {"status": "observed_local_registry_only", "items": [entry, dict(entry)]}
    with pytest.raises(ValueError, match="Duplicate local geo code"):
        compare_catalogs(official, local)


def test_catalog_count_mismatch_is_rejected():
    official = {"scope": "official_gisco_nuts_2024_catalog_only",
                "catalogs": {level: {code: {"codes": [code+"11"], "count": 2}
                            for code in ("ES", "IE", "PT")}
                             for level in ("nuts2", "nuts3")}}
    with pytest.raises(ValueError, match="Incomplete official catalog"):
        compare_catalogs(official, {"status": "observed_local_registry_only", "items": []})
