"""One-shot national acceptance: synthetic evidence and API validation."""
from scripts.accept_national_compare import accept


def fixture():
    ids = [f"id_{n}" for n in range(29)]
    rows = [{"country_iso3": country, "indicator_id": item,
             "period": 2025, "source_id": "EUROSTAT" if n else "IMF",
             "value": float(n), "unit": "percent"}
            for country in ("ESP", "IRL") for n, item in enumerate(ids)]
    # Require exactly six IMF rows: three per country.
    for row in rows:
        if row["indicator_id"] in {"id_0", "id_1", "id_2"}:
            row["source_id"] = "IMF"
    api = {"countries": [{"iso3": "ESP"}, {"iso3": "IRL"}],
           "indicator_count": 29,
           "indicators": [{"indicator_id": item, "countries": {
               country: {"period": 2025, "source_id": "IMF" if n < 3 else "EUROSTAT", "value": float(n)}
               for country in ("ESP", "IRL")}}
               for n, item in enumerate(ids)]}
    audited = {"rows": 58, "status_counts": {"match": 52, "vintage_unverifiable": 6},
               "results": [{"provider": row["source_id"],
                            "status": "vintage_unverifiable" if row["source_id"] == "IMF" else "match",
                            "country": row["country_iso3"], "indicator_id": row["indicator_id"]}
                           for row in rows]}
    evidence = {"rows": rows, "country_counts": {"ESP": 29, "IRL": 29}}
    return evidence, audited, api


def test_operator_acceptance_reaches_explicit_imf_block():
    result = accept(*fixture())
    assert result["api_alignment"] == "pass"
    assert result["verified_observations"] == 52
    assert result["status"] == "blocked"
    assert len(result["imf_vintage_gates"]) == 6
    assert not result["acceptance_findings"]


def test_api_value_mismatch_is_detected():
    evidence, audited, api = fixture()
    api["indicators"][4]["countries"]["ESP"]["value"] = 900
    result = accept(evidence, audited, api)
    assert result["api_alignment"] == "fail"
    assert any("API changed" in value for value in result["acceptance_findings"])


def test_revision_not_silently_accepted():
    evidence, audited, api = fixture()
    audited["results"][0]["status"] = "value_drift"
    audited["status_counts"] = {"match": 52, "vintage_unverifiable": 5, "value_drift": 1}
    result = accept(evidence, audited, api)
    assert result["status"] == "blocked"
    assert len(result["open_source_discrepancies"]) == 1
