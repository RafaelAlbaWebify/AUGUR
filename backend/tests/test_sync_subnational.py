from app.catalog import COUNTRIES
from scripts import sync_subnational as module


def test_default_subnational_countries_follow_registered_eu_catalog():
    expected = [
        country["iso3"]
        for country in COUNTRIES
        if country.get("eu_member")
    ]

    assert module.DEFAULT_COUNTRIES == expected
    assert module.DEFAULT_COUNTRIES == ["ESP", "PRT", "IRL"]
