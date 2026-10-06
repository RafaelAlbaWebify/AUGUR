from app.ingestion.cedefop_stas import detect_table_schema


def test_detects_country_isco_year_and_growth_metric():
    rows = [
        ["Cedefop STAS dataset"],
        [],
        ["Country", "ISCO code", "Year", "Employment change (% growth)", "Baseline"],
        ["Spain", "25", 2027, 2.4, "AMECO"],
    ]

    result = detect_table_schema(rows)

    assert result["status"] == "recognised"
    assert result["header_row_index"] == 2
    assert result["matches"]["country"] == 0
    assert result["matches"]["isco"] == 1
    assert result["matches"]["year"] == 2
    assert result["matches"]["growth_pct"] == 3


def test_partial_schema_is_not_marked_ready():
    rows = [
        ["Country", "Year", "Value"],
        ["Spain", 2027, 1.2],
    ]

    result = detect_table_schema(rows)

    assert result["status"] == "partial"
    assert result["core_fields_present"] is False
    assert result["metric_present"] is False


def test_unrelated_sheet_is_unrecognised():
    rows = [
        ["Notes", "Description"],
        ["Method", "VAR / VECM / ARIMA"],
    ]

    result = detect_table_schema(rows)

    assert result["status"] == "unrecognised"


def test_detects_stas_august_2026_wide_one_digit_schema():
    rows = [
        ["metadata"],
        [],
        ["scenario", "country", "country_code", "Occupations (1-digit)", "oc_code", "2026", "2027"],
        ["Aligned_forecast_Ameco", "Spain", "ES", "Professionals", 2, 1000.0, 1030.0],
    ]

    result = detect_table_schema(rows, "ameco_1d_%")

    assert result["status"] == "recognised"
    assert result["header_row_index"] == 2
    assert result["matches"]["country"] == 1
    assert result["matches"]["country_code"] == 2
    assert result["matches"]["isco"] == 4
    assert result["year_columns"] == {2026: 5, 2027: 6}
    assert result["metric_kind"] == "growth_pct"


def test_detects_stas_level_sheet_from_sheet_name():
    rows = [
        ["scenario", "country", "country_code", "Occupations (1-digit)", "oc_code", "2026", "2027"],
        ["Aligned_forecast_Ameco", "Spain", "ES", "Professionals", 2, 1000.0, 1030.0],
    ]

    result = detect_table_schema(rows, "ameco_1d")

    assert result["status"] == "recognised"
    assert result["metric_kind"] == "employment_level_thousands"
    assert result["metric_present"] is True


def test_detects_wide_year_columns():
    from app.ingestion.cedefop_stas import _year_columns

    result = _year_columns(["scenario", "country", "2026", "2027"])

    assert result == {2026: 2, 2027: 3}


def test_parse_stas_combines_levels_and_growth(monkeypatch, tmp_path):
    from app.ingestion import cedefop_stas as stas

    monkeypatch.setattr(
        stas,
        "workbook_preview",
        lambda _path, max_rows=100000: [
            {
                "sheet": "ameco_2d",
                "rows": [
                    ["scenario", "country", "country_code", "oc", "oc_code", 2026, 2027],
                    ["Aligned_forecast_Ameco", "Spain", "ES", "ICT professionals", 25, 100.0, 103.14],
                ],
            },
            {
                "sheet": "ameco_2d_%",
                "rows": [
                    ["scenario", "country", "country_code", "oc", "oc_code", 2026, 2027],
                    ["Aligned_forecast_Ameco", "Spain", "ES", "ICT professionals", 25, 0.01, 0.0314],
                ],
            },
        ],
    )

    rows = stas.parse_stas_workbook(tmp_path / "stas.xlsx")

    assert len(rows) == 2
    row_2027 = next(row for row in rows if row["period"] == 2027)
    assert row_2027["country_iso3"] == "ESP"
    assert row_2027["isco08"] == "25"
    assert row_2027["isco_level"] == 2
    assert row_2027["employment_level_thousands"] == 103.14
    assert round(row_2027["employment_growth_pct"], 2) == 3.14
    assert row_2027["release_version"] == "2026-08"
