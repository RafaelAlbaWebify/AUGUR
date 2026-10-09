from scripts.audit_official_nuts_catalog import official_codes


def test_catalog_codes_are_deduplicated_and_country_scoped():
    features = [
        {"properties": {"CNTR_CODE": "ES", "NUTS_ID": "ES11"}},
        {"properties": {"CNTR_CODE": "ES", "NUTS_ID": "ES11"}},
        {"properties": {"CNTR_CODE": "IE", "NUTS_ID": "IE04"}},
        {"properties": {"CNTR_CODE": "FR", "NUTS_ID": "FR10"}},
    ]
    assert official_codes(features, {"ES", "IE", "PT"}) == {
        "ES": ["ES11"], "IE": ["IE04"], "PT": [],
    }
