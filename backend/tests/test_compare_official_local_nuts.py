from scripts.compare_official_local_nuts import compare_catalogs


def test_code_membership_not_confused_with_statistical_coverage():
    official = {
        "scope": "official_gisco_nuts_2024_catalog_only",
        "catalogs": {
            level: {
                iso2: {"codes": (["ES11", "ES12"] if level == "nuts2" and iso2 == "ES" else [])}
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
