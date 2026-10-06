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
