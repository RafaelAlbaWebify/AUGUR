from types import SimpleNamespace

from scripts import ensure_local_evidence as module


def test_regional_sector_evidence_noops_when_already_available(monkeypatch):
    status = {
        "available": True,
        "row_count": 12,
        "region_count": 3,
        "country_prefixes": ["ES", "IE", "PT"],
        "nace_code_count": 4,
        "latest_period": 2025,
        "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
        "geo_level": "NUTS2",
    }

    monkeypatch.setattr(
        module,
        "regional_sector_employment_status",
        lambda: status,
    )

    class UnexpectedAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("network adapter should not be created")

    monkeypatch.setattr(module, "EurostatAdapter", UnexpectedAdapter)

    result = module.ensure_regional_sector_evidence()

    assert result["status"] == "available"
    assert result["action"] == "none"
    assert result["before"] == status
    assert result["after"] == status


def test_regional_sector_evidence_repairs_missing_store(monkeypatch):
    statuses = iter([
        {
            "available": False,
            "row_count": 0,
            "region_count": 0,
            "country_prefixes": [],
            "nace_code_count": 0,
            "latest_period": None,
            "latest_retrieved_at": None,
            "geo_level": "NUTS2",
        },
        {
            "available": True,
            "row_count": 2,
            "region_count": 1,
            "country_prefixes": ["ES"],
            "nace_code_count": 2,
            "latest_period": 2025,
            "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
            "geo_level": "NUTS2",
        },
    ])

    monkeypatch.setattr(
        module,
        "regional_sector_employment_status",
        lambda: next(statuses),
    )

    class FakeAdapter:
        def __init__(self, *args, **kwargs):
            self.closed = False

        def close(self):
            self.closed = True

    monkeypatch.setattr(module, "EurostatAdapter", FakeAdapter)
    monkeypatch.setattr(
        module,
        "fetch_regional_sector_employment",
        lambda adapter: (
            [
                {
                    "geo_code": "ES12",
                    "geo_name": "Principado de Asturias",
                    "geo_level": "NUTS2",
                    "period": 2025,
                    "nace_code": "TOTAL",
                    "nace_label": "Total",
                    "employment_thousands": 400.0,
                    "source_id": "EUROSTAT",
                    "dataset_id": "lfst_r_lfe2en2",
                    "retrieved_at": "2026-10-07T00:00:00+00:00",
                    "source_updated_at": None,
                },
                {
                    "geo_code": "ES12",
                    "geo_name": "Principado de Asturias",
                    "geo_level": "NUTS2",
                    "period": 2025,
                    "nace_code": "J",
                    "nace_label": "Information and communication",
                    "employment_thousands": 20.0,
                    "source_id": "EUROSTAT",
                    "dataset_id": "lfst_r_lfe2en2",
                    "retrieved_at": "2026-10-07T00:00:00+00:00",
                    "source_updated_at": None,
                },
            ],
            {"status": "available"},
        ),
    )
    monkeypatch.setattr(
        module,
        "upsert_regional_sector_employment",
        lambda rows: len(rows),
    )

    result = module.ensure_regional_sector_evidence()

    assert result["status"] == "available"
    assert result["action"] == "repaired"
    assert result["rows_parsed"] == 2
    assert result["rows_upserted"] == 2


def test_main_returns_partial_when_repair_cannot_restore_evidence(monkeypatch, capsys):
    monkeypatch.setattr(module, "initialize_datastores", lambda: None)
    monkeypatch.setattr(
        module,
        "ensure_regional_sector_evidence",
        lambda: {
            "evidence_id": "regional_sector_employment",
            "status": "missing",
            "action": "repair_failed",
        },
    )

    code = module.main()

    assert code == 2
    output = capsys.readouterr().out
    assert '"status": "partial"' in output
    assert '"regional_sector_employment"' in output
