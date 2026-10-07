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
    monkeypatch.setattr(
        module,
        "ensure_nuts3_safety_evidence",
        lambda: {
            "evidence_id": "nuts3_safety",
            "status": "available",
            "action": "none",
        },
    )
    monkeypatch.setattr(
        module,
        "ensure_clssi_evidence",
        lambda: {
            "evidence_id": "cedefop_clssi",
            "status": "available",
            "action": "none",
        },
    )
    monkeypatch.setattr(
        module,
        "ensure_oja_imbalance_evidence",
        lambda: {
            "evidence_id": "cedefop_oja_imbalance",
            "status": "available",
            "action": "none",
        },
    )

    code = module.main()

    assert code == 2
    output = capsys.readouterr().out
    assert '"status": "partial"' in output
    assert '"regional_sector_employment"' in output



def test_nuts3_safety_noops_when_already_available(monkeypatch):
    levels = {
        "NUTS3": {
            "available": True,
            "row_count": 20,
            "geography_count": 10,
            "country_prefixes": ["ES", "IE", "PT"],
            "indicator_ids": [
                "regional_intentional_homicide_rate",
                "regional_robbery_rate",
            ],
            "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
            "geo_level": "NUTS3",
        }
    }

    monkeypatch.setattr(
        module,
        "subnational_evidence_by_level_status",
        lambda: levels,
    )

    class UnexpectedClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("GISCO network should not be used")

    monkeypatch.setattr(module.httpx, "Client", UnexpectedClient)

    result = module.ensure_nuts3_safety_evidence()

    assert result["status"] == "available"
    assert result["action"] == "none"
    assert result["before"] == levels["NUTS3"]


def test_nuts3_safety_repairs_missing_store(monkeypatch):
    statuses = iter([
        {
            "NUTS3": {
                "available": False,
                "row_count": 0,
                "geography_count": 0,
                "country_prefixes": [],
                "indicator_ids": [],
                "latest_retrieved_at": None,
                "geo_level": "NUTS3",
            }
        },
        {
            "NUTS3": {
                "available": True,
                "row_count": 6,
                "geography_count": 3,
                "country_prefixes": ["ES", "IE", "PT"],
                "indicator_ids": [
                    "regional_intentional_homicide_rate",
                    "regional_robbery_rate",
                ],
                "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
                "geo_level": "NUTS3",
            }
        },
    ])
    monkeypatch.setattr(
        module,
        "subnational_evidence_by_level_status",
        lambda: next(statuses),
    )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "properties": {
                            "NUTS_ID": "ES120",
                            "CNTR_CODE": "ES",
                        }
                    },
                    {
                        "properties": {
                            "NUTS_ID": "PT170",
                            "CNTR_CODE": "PT",
                        }
                    },
                    {
                        "properties": {
                            "NUTS_ID": "IE061",
                            "CNTR_CODE": "IE",
                        }
                    },
                    {
                        "properties": {
                            "NUTS_ID": "BG411",
                            "CNTR_CODE": "BG",
                        }
                    },
                ],
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url):
            assert url == module.NUTS3_URL
            return FakeResponse()

    monkeypatch.setattr(module.httpx, "Client", FakeClient)

    seen = {}
    def fake_sync(codes):
        seen["codes"] = codes
        return {
            "geo_code_count": len(codes),
            "geographies_with_data": len(codes),
            "rows_upserted": len(codes) * 2,
            "results": [],
        }

    monkeypatch.setattr(
        module,
        "sync_regional_evidence_codes",
        fake_sync,
    )

    result = module.ensure_nuts3_safety_evidence()

    assert seen["codes"] == ["ES120", "IE061", "PT170"]
    assert result["status"] == "available"
    assert result["action"] == "repaired"
    assert result["region_count_requested"] == 3
    assert result["sync_result"]["rows_upserted"] == 6



def test_clssi_evidence_noops_when_already_available(monkeypatch):
    status = {
        "available": True,
        "row_count": 129,
        "country_count": 3,
        "countries": ["ESP", "IRL", "PRT"],
        "horizons": [2035],
        "release_versions": ["2026"],
        "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
    }
    monkeypatch.setattr(
        module,
        "labour_shortage_index_status",
        lambda: status,
    )

    def unexpected_download(path):
        raise AssertionError("CLSSI download should not run")

    monkeypatch.setattr(
        module,
        "download_clssi_workbook",
        unexpected_download,
    )

    result = module.ensure_clssi_evidence()

    assert result["status"] == "available"
    assert result["action"] == "none"
    assert result["before"] == status
    assert result["after"] == status


def test_clssi_evidence_repairs_missing_store(monkeypatch, tmp_path):
    statuses = iter([
        {
            "available": False,
            "row_count": 0,
            "country_count": 0,
            "countries": [],
            "horizons": [],
            "release_versions": [],
            "latest_retrieved_at": None,
        },
        {
            "available": True,
            "row_count": 3,
            "country_count": 3,
            "countries": ["ESP", "IRL", "PRT"],
            "horizons": [2035],
            "release_versions": ["2026"],
            "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
        },
    ])
    monkeypatch.setattr(
        module,
        "labour_shortage_index_status",
        lambda: next(statuses),
    )
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(data_dir=tmp_path),
    )

    downloaded = {}
    monkeypatch.setattr(
        module,
        "download_clssi_workbook",
        lambda path: downloaded.setdefault(
            "result",
            {
                "url": "https://example.test/clssi.xlsx",
                "path": str(path),
                "bytes": 100,
                "content_type": "application/xlsx",
            },
        ),
    )

    rows = [
        {
            "country_iso3": "ESP",
            "horizon": 2035,
            "isco08": "25",
        },
        {
            "country_iso3": "IRL",
            "horizon": 2035,
            "isco08": "25",
        },
        {
            "country_iso3": "PRT",
            "horizon": 2035,
            "isco08": "25",
        },
    ]
    monkeypatch.setattr(
        module,
        "parse_clssi_workbook",
        lambda path: rows,
    )
    monkeypatch.setattr(
        module,
        "upsert_labour_shortage_index",
        lambda parsed: len(parsed),
    )

    result = module.ensure_clssi_evidence()

    assert result["status"] == "available"
    assert result["action"] == "repaired"
    assert result["rows_parsed"] == 3
    assert result["rows_upserted"] == 3
    assert result["download"]["bytes"] == 100



def test_oja_imbalance_evidence_noops_when_already_available(monkeypatch):
    status = {
        "available": True,
        "row_count": 308,
        "release_versions": ["2026-05"],
        "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
        "geographic_scope": "EU27",
    }
    monkeypatch.setattr(
        module,
        "labour_oja_imbalance_eu27_status",
        lambda: status,
    )

    def unexpected_download(path):
        raise AssertionError("OJA imbalance download should not run")

    monkeypatch.setattr(
        module,
        "download_oja_imbalance_csv",
        unexpected_download,
    )

    result = module.ensure_oja_imbalance_evidence()

    assert result["status"] == "available"
    assert result["action"] == "none"
    assert result["before"] == status
    assert result["after"] == status


def test_oja_imbalance_evidence_repairs_missing_store(monkeypatch, tmp_path):
    statuses = iter([
        {
            "available": False,
            "row_count": 0,
            "release_versions": [],
            "latest_retrieved_at": None,
            "geographic_scope": "EU27",
        },
        {
            "available": True,
            "row_count": 2,
            "release_versions": ["2026-05"],
            "latest_retrieved_at": "2026-10-07T00:00:00+00:00",
            "geographic_scope": "EU27",
        },
    ])
    monkeypatch.setattr(
        module,
        "labour_oja_imbalance_eu27_status",
        lambda: next(statuses),
    )
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(data_dir=tmp_path),
    )
    monkeypatch.setattr(
        module,
        "download_oja_imbalance_csv",
        lambda path: {
            "url": "https://www.cedefop.europa.eu/files/cedefop-oja-imbalance-2026-05.csv",
            "path": str(path),
            "bytes": 1234,
            "content_type": "text/csv",
            "release_version": "2026-05",
        },
    )

    rows = [
        {
            "isco08": "2522",
            "score": 0.62,
        },
        {
            "isco08": "3512",
            "score": 0.41,
        },
    ]
    monkeypatch.setattr(
        module,
        "parse_oja_imbalance_csv",
        lambda path: rows,
    )
    monkeypatch.setattr(
        module,
        "upsert_labour_oja_imbalance_eu27",
        lambda parsed: len(parsed),
    )

    result = module.ensure_oja_imbalance_evidence()

    assert result["status"] == "available"
    assert result["action"] == "repaired"
    assert result["rows_parsed"] == 2
    assert result["rows_upserted"] == 2
    assert result["download"]["content_type"] == "text/csv"
