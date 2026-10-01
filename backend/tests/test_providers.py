from app.providers import PROVIDERS, providers_for_country


def test_provider_ids_are_unique():
    ids = [provider.provider_id for provider in PROVIDERS]
    assert len(ids) == len(set(ids))


def test_spain_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("ESP")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}


def test_portugal_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("PRT")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}


def test_ireland_uses_all_core_providers():
    ids = {provider.provider_id for provider in providers_for_country("IRL")}
    assert ids == {"WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"}
