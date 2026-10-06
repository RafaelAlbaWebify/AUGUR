from app.services import eea_city_catalog as module


def test_resolve_eea_city_uses_cached_mapping(monkeypatch):
    monkeypatch.setattr(
        module,
        "_CACHE",
        (
            module.monotonic(),
            {
                "IE001C": {
                    "city_code": "IE001C",
                    "country_code": "IE",
                    "eea_city_name": "Dublin",
                    "gisco_city_name": "Dublin (greater city)",
                    "match_method": "normalized_exact",
                }
            },
        ),
    )

    result = module.resolve_eea_city("ie001c")

    assert result is not None
    assert result["eea_city_name"] == "Dublin"
    assert result["country_code"] == "IE"
