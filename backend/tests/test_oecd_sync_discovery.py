from scripts import sync_oecd_fua, sync_oecd_regional


def _exercise_autodiscovery(monkeypatch, module):
    registry_state = [
        {
            "iso2": "ES",
            "iso3": "ESP",
            "eu_member": True,
            "oecd_member": True,
        }
    ]
    calls = {
        "catalog": 0,
        "single": [],
    }

    monkeypatch.setattr(
        module,
        "OECD_MEMBER_ISO3",
        {"ESP", "AUS", "CAN", "USA", "JPN"},
    )
    monkeypatch.setattr(
        module,
        "EU_MEMBER_ISO3",
        {"ESP"},
    )
    monkeypatch.setattr(
        module,
        "country_registry",
        lambda: list(registry_state),
    )

    class FakeWorldBank:
        def __init__(self, *args, **kwargs):
            pass

        def register_country_catalog(self):
            calls["catalog"] += 1
            registry_state.extend([
                {
                    "iso2": "AU",
                    "iso3": "AUS",
                    "eu_member": False,
                    "oecd_member": True,
                },
                {
                    "iso2": "CA",
                    "iso3": "CAN",
                    "eu_member": False,
                    "oecd_member": True,
                },
                {
                    "iso2": "US",
                    "iso3": "USA",
                    "eu_member": False,
                    "oecd_member": True,
                },
                {
                    "iso2": "JP",
                    "iso3": "JPN",
                    "eu_member": False,
                    "oecd_member": True,
                },
            ])

        def ensure_country_registered(self, code):
            calls["single"].append(code)

        def close(self):
            pass

    monkeypatch.setattr(module, "WorldBankAdapter", FakeWorldBank)

    result = module._target_countries(None)

    assert result == {"AUS", "CAN", "USA", "JPN"}
    assert calls["catalog"] == 1
    assert calls["single"] == []


def test_regional_sync_autodiscovers_non_eu_oecd_countries(monkeypatch):
    _exercise_autodiscovery(monkeypatch, sync_oecd_regional)


def test_urban_sync_autodiscovers_non_eu_oecd_countries(monkeypatch):
    _exercise_autodiscovery(monkeypatch, sync_oecd_fua)


def _exercise_explicit_registration(monkeypatch, module):
    registry_state = []

    monkeypatch.setattr(
        module,
        "country_registry",
        lambda: list(registry_state),
    )
    monkeypatch.setattr(
        module,
        "country_record",
        lambda code: next(
            (
                item
                for item in registry_state
                if item["iso3"] == code
            ),
            None,
        ),
    )

    class FakeWorldBank:
        def __init__(self, *args, **kwargs):
            pass

        def register_country_catalog(self):
            raise AssertionError("Explicit selection should not download full catalog")

        def ensure_country_registered(self, code):
            registry_state.append({
                "iso2": "AU" if code == "AUS" else "DE",
                "iso3": code,
                "eu_member": code == "DEU",
                "oecd_member": True,
            })

        def close(self):
            pass

    monkeypatch.setattr(module, "WorldBankAdapter", FakeWorldBank)

    result = module._target_countries(["AUS", "DEU"])

    assert result == {"AUS"}


def test_regional_sync_explicit_selection_registers_only_requested(monkeypatch):
    _exercise_explicit_registration(monkeypatch, sync_oecd_regional)


def test_urban_sync_explicit_selection_registers_only_requested(monkeypatch):
    _exercise_explicit_registration(monkeypatch, sync_oecd_fua)


def test_regional_sync_skips_network_when_local_evidence_is_fresh(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(sync_oecd_regional, "initialize_datastores", lambda: None)
    monkeypatch.setattr(
        sync_oecd_regional,
        "_target_countries",
        lambda requested: {"AUS", "CAN"},
    )
    monkeypatch.setattr(
        sync_oecd_regional,
        "stale_geography_countries",
        lambda system, countries, required, max_age_hours=24.0: set(),
    )

    class UnexpectedAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Fresh evidence must not create an OECD client")

    monkeypatch.setattr(
        sync_oecd_regional,
        "OECDRegionalAdapter",
        UnexpectedAdapter,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["sync_oecd_regional"],
    )

    assert sync_oecd_regional.main() == 0
    output = capsys.readouterr().out
    assert '"status": "fresh_local_evidence"' in output
    assert '"AUS"' in output
    assert '"CAN"' in output


def test_urban_sync_skips_network_when_local_evidence_is_fresh(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(sync_oecd_fua, "initialize_datastores", lambda: None)
    monkeypatch.setattr(
        sync_oecd_fua,
        "_target_countries",
        lambda requested: {"AUS"},
    )
    monkeypatch.setattr(
        sync_oecd_fua,
        "stale_geography_countries",
        lambda system, countries, required, max_age_hours=24.0: set(),
    )

    class UnexpectedAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Fresh evidence must not create an OECD client")

    monkeypatch.setattr(
        sync_oecd_fua,
        "OECDFUAAdapter",
        UnexpectedAdapter,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["sync_oecd_fua"],
    )

    assert sync_oecd_fua.main() == 0
    output = capsys.readouterr().out
    assert '"status": "fresh_local_evidence"' in output
    assert '"AUS"' in output
