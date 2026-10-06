from app.ingestion.cedefop_oja_imbalance import detect_schema


def test_detects_occupation_code_and_score():
    result = detect_schema([
        "isco_code",
        "occupation",
        "score",
    ])

    assert result["status"] == "recognised"
    assert result["matches"]["occupation_code"] == 0
    assert result["matches"]["occupation_label"] == 1
    assert result["matches"]["score"] == 2
    assert result["ready_for_parser_implementation"] is True


def test_partial_schema_is_not_ready():
    result = detect_schema([
        "occupation",
        "value",
    ])

    assert result["status"] == "partial"
    assert result["ready_for_parser_implementation"] is False
