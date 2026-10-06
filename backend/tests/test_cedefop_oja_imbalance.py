from app.ingestion.cedefop_oja_imbalance import detect_schema


def test_detects_occupation_code_and_score():
    result = detect_schema([
        "ISCO_1",
        "ISCO_4",
        "Occupation",
        "score",
    ])

    assert result["status"] == "recognised"
    assert result["matches"]["major_group"] == 0
    assert result["matches"]["occupation_code"] == 1
    assert result["matches"]["occupation_label"] == 2
    assert result["matches"]["score"] == 3
    assert result["ready_for_parser_implementation"] is True


def test_partial_schema_is_not_ready():
    result = detect_schema([
        "occupation",
        "value",
    ])

    assert result["status"] == "partial"
    assert result["ready_for_parser_implementation"] is False
