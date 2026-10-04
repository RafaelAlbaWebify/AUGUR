from app.ingestion.eurostat import EurostatAdapter


def test_eurostat_normalization_uses_requested_country():
    payload = {
        "id": ["geo", "time"],
        "size": [1, 2],
        "dimension": {
            "geo": {
                "category": {
                    "index": {"PT": 0},
                }
            },
            "time": {
                "category": {
                    "index": {"2023": 0, "2024": 1},
                }
            },
        },
        "value": [10.4, 10.6],
        "updated": "2026-09-01",
    }

    config = {
        "indicator_id": "population_total",
        "dataset_id": "synthetic",
        "filters": {"geo": "__GEO__"},
        "unit": "persons",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize("PRT", config, payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["country_iso3"] for row in rows} == {"PRT"}
    assert rows[-1]["period"] == 2024


def test_eurostat_earnings_normalization_keeps_isco_dimension():
    payload = {
        "id": ["geo", "isco08", "time"],
        "size": [1, 3, 1],
        "dimension": {
            "geo": {"category": {"index": {"ES": 0}}},
            "isco08": {
                "category": {
                    "index": {"TOTAL": 0, "OC2": 1, "OC3": 2},
                }
            },
            "time": {"category": {"index": {"2022": 0}}},
        },
        "value": [3000.0, 4100.0, 3200.0],
        "updated": "2026-02-09",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize_earnings("ESP", payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["isco08"] for row in rows} == {"OC2", "OC3"}
    assert {row["period"] for row in rows} == {2022}
    assert {row["unit"] for row in rows} == {"eur_gross_monthly"}
    assert {row["dataset_id"] for row in rows} == {"earn_ses22_21"}


def test_eurostat_job_transition_normalization_keeps_probability_context():
    payload = {
        "id": ["geo", "age", "duration", "time"],
        "size": [1, 1, 1, 2],
        "dimension": {
            "geo": {"category": {"index": {"IE": 0}}},
            "age": {"category": {"index": {"Y15-74": 0}}},
            "duration": {"category": {"index": {"TOTAL": 0}}},
            "time": {"category": {"index": {"2024": 0, "2025": 1}}},
        },
        "value": [37.0, 38.0],
        "updated": "2026-06-11",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize_job_transitions("IRL", payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert rows[-1]["country_iso3"] == "IRL"
    assert rows[-1]["period"] == 2025
    assert rows[-1]["age_group"] == "Y15-74"
    assert rows[-1]["duration_group"] == "TOTAL"
    assert rows[-1]["probability_pct"] == 38.0
    assert rows[-1]["dataset_id"] == "lfsi_long_e01"


def test_eurostat_net_earnings_normalization_preserves_standard_case():
    payload = {
        "id": ["geo", "ecase", "time"],
        "size": [1, 1, 2],
        "dimension": {
            "geo": {"category": {"index": {"ES": 0}}},
            "ecase": {
                "category": {
                    "index": {"P1_NCH_AW100": 0},
                }
            },
            "time": {
                "category": {
                    "index": {"2024": 0, "2025": 1},
                }
            },
        },
        "value": [30000.0, 31500.0],
        "updated": "2026-09-04",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize_net_earnings("ESP", payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert rows[-1]["country_iso3"] == "ESP"
    assert rows[-1]["period"] == 2025
    assert rows[-1]["earnings_case"] == "P1_NCH_AW100"
    assert rows[-1]["annual_net_eur"] == 31500.0
    assert rows[-1]["dataset_id"] == "earn_nt_net"


def test_eurostat_job_transition_normalization_keeps_all_age_classes():
    payload = {
        "id": ["geo", "age", "duration", "time"],
        "size": [1, 4, 1, 1],
        "dimension": {
            "geo": {"category": {"index": {"IE": 0}}},
            "age": {
                "category": {
                    "index": {
                        "Y15-24": 0,
                        "Y25-54": 1,
                        "Y55-74": 2,
                        "Y15-74": 3,
                    },
                }
            },
            "duration": {"category": {"index": {"TOTAL": 0}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": [31.0, 39.0, 22.0, 35.0],
        "updated": "2026-06-11",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize_job_transitions("IRL", payload)
    finally:
        adapter.close()

    assert len(rows) == 4
    assert {row["age_group"] for row in rows} == {
        "Y15-24",
        "Y25-54",
        "Y55-74",
        "Y15-74",
    }


def test_eurostat_job_vacancy_normalization_keeps_major_isco_and_aggregate_nace():
    payload = {
        "id": [
            "geo",
            "s_adj",
            "nace_r21",
            "sizeclas",
            "isco08",
            "indic_em",
            "time",
        ],
        "size": [1, 1, 2, 1, 4, 1, 1],
        "dimension": {
            "geo": {"category": {"index": {"ES": 0}}},
            "s_adj": {"category": {"index": {"SA": 0}}},
            "nace_r21": {
                "category": {
                    "index": {"B-T": 0, "J": 1},
                }
            },
            "sizeclas": {"category": {"index": {"TOTAL": 0}}},
            "isco08": {
                "category": {
                    "index": {
                        "TOTAL": 0,
                        "OC2": 1,
                        "OC3": 2,
                        "OC1-3": 3,
                    },
                }
            },
            "indic_em": {"category": {"index": {"JVR": 0}}},
            "time": {"category": {"index": {"2026-Q2": 0}}},
        },
        "value": [
            2.0,
            3.5,
            2.8,
            3.1,
            1.9,
            4.2,
            3.8,
            4.0,
        ],
        "updated": "2026-09-15",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize_job_vacancy_rates("ESP", payload)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert {row["isco08"] for row in rows} == {"OC2", "OC3"}
    assert {row["nace_scope"] for row in rows} == {"B-T"}
    assert {row["period"] for row in rows} == {"2026-Q2"}
    assert {row["dataset_id"] for row in rows} == {"jvs_q_isco_r21"}
    assert {row["vacancy_rate_pct"] for row in rows} == {3.5, 2.8}


def test_eurostat_job_vacancy_normalization_refuses_unknown_aggregate_scope():
    payload = {
        "id": [
            "geo",
            "nace_r21",
            "isco08",
            "time",
        ],
        "size": [1, 1, 1, 1],
        "dimension": {
            "geo": {"category": {"index": {"ES": 0}}},
            "nace_r21": {"category": {"index": {"J": 0}}},
            "isco08": {"category": {"index": {"OC2": 0}}},
            "time": {"category": {"index": {"2026-Q2": 0}}},
        },
        "value": [3.5],
        "updated": "2026-09-15",
    }

    adapter = EurostatAdapter(client=None)
    try:
        try:
            adapter.normalize_job_vacancy_rates("ESP", payload)
        except ValueError as exc:
            assert "aggregate NACE scope" in str(exc)
        else:
            raise AssertionError("expected aggregate NACE scope validation")
    finally:
        adapter.close()


def test_eurostat_normalization_can_select_rate_unit_by_human_label():
    payload = {
        "id": ["geo", "unit", "time"],
        "size": [1, 2, 2],
        "dimension": {
            "geo": {"category": {"index": {"ES": 0}}},
            "unit": {
                "category": {
                    "index": {"NR": 0, "RATE": 1},
                    "label": {
                        "NR": "Number",
                        "RATE": "Rate",
                    },
                }
            },
            "time": {"category": {"index": {"2022": 0, "2023": 1}}},
        },
        "value": [12000.0, 11000.0, 24.0, 21.0],
        "updated": "2026-09-01",
    }
    config = {
        "indicator_id": "pm25_premature_death_rate",
        "dataset_id": "sdg_11_52",
        "filters": {"geo": "__GEO__", "freq": "A"},
        "label_contains": {"unit": "Rate"},
        "unit": "per_100k_people",
    }

    adapter = EurostatAdapter(client=None)
    try:
        rows = adapter.normalize("ESP", config, payload)
    finally:
        adapter.close()

    assert [row["value"] for row in rows] == [24.0, 21.0]
    assert [row["period"] for row in rows] == [2022, 2023]
    assert {row["unit"] for row in rows} == {"per_100k_people"}
