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
