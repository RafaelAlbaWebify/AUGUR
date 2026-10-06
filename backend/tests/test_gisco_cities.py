from app.ingestion.gisco_cities import (
    canonical_city_match_name,
    city_code,
    gisco_city_catalog,
    match_eea_cities_to_gisco,
    normalize_city_name,
)


def test_normalize_city_name_handles_accents_and_punctuation():
    assert normalize_city_name("A Coruña") == "a coruna"
    assert normalize_city_name("Donostia / San Sebastián") == "donostia san sebastian"


def test_city_code_finds_urban_audit_code():
    feature = {
        "properties": {
            "NAME_LATN": "Oviedo",
            "URAU_CODE": "ES012C",
        }
    }
    assert city_code(feature) == "ES012C"


def test_exact_normalized_city_match_is_safe():
    payload = {
        "features": [
            {
                "properties": {
                    "NAME_LATN": "A Coruña",
                    "URAU_CODE": "ES013C",
                }
            },
            {
                "properties": {
                    "NAME_LATN": "Oviedo",
                    "URAU_CODE": "ES012C",
                }
            },
        ]
    }
    gisco = gisco_city_catalog(payload, {"ES"})
    result = match_eea_cities_to_gisco(
        gisco,
        [
            {"countryCode": "ES", "cityName": "A Coruna"},
            {"countryCode": "ES", "cityName": "Oviedo"},
            {"countryCode": "ES", "cityName": "Nonexistent"},
        ],
    )

    assert result["matched_count"] == 2
    assert result["unmatched_count"] == 1
    assert result["ambiguous_count"] == 0
    assert {
        row["city_code"] for row in result["matched"]
    } == {"ES013C", "ES012C"}


def test_ambiguous_normalized_match_is_rejected():
    gisco = [
        {
            "city_code": "ES001C",
            "country_code": "ES",
            "city_name": "Example",
            "normalized_name": "example",
        },
        {
            "city_code": "ES002C",
            "country_code": "ES",
            "city_name": "Example",
            "normalized_name": "example",
        },
    ]
    result = match_eea_cities_to_gisco(
        gisco,
        [{"countryCode": "ES", "cityName": "Example"}],
    )

    assert result["matched_count"] == 0
    assert result["ambiguous_count"] == 1


def test_canonical_match_ignores_only_greater_city_suffix():
    assert canonical_city_match_name("Dublin (greater city)") == "dublin"
    assert canonical_city_match_name("Dublin") == "dublin"
    assert canonical_city_match_name("Porto (greater city)") == "porto"


def test_greater_city_variants_match_without_fuzzy_logic():
    gisco = [
        {
            "city_code": "IE001C",
            "country_code": "IE",
            "city_name": "Dublin (greater city)",
            "normalized_name": "dublin greater city",
            "match_name": "dublin",
        },
        {
            "city_code": "PT002C",
            "country_code": "PT",
            "city_name": "Porto",
            "normalized_name": "porto",
            "match_name": "porto",
        },
    ]
    result = match_eea_cities_to_gisco(
        gisco,
        [
            {"countryCode": "IE", "cityName": "Dublin"},
            {"countryCode": "PT", "cityName": "Porto (greater city)"},
        ],
    )

    assert result["matched_count"] == 2
    assert result["ambiguous_count"] == 0
    assert {row["city_code"] for row in result["matched"]} == {
        "IE001C",
        "PT002C",
    }
