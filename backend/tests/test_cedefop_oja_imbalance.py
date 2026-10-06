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


def test_parse_published_oja_csv(tmp_path):
    from app.ingestion.cedefop_oja_imbalance import parse_csv

    path = tmp_path / "oja.csv"
    path.write_text(
        "ISCO_1,ISCO_4,Occupation,score\n"
        "2 Professionals,2522,Systems administrators,0.625\n"
        "3 Technicians,3512,ICT user support technicians,0.41\n",
        encoding="utf-8",
    )

    rows = parse_csv(path)

    assert len(rows) == 2
    assert rows[0]["isco08"] == "2522"
    assert rows[0]["occupation_label"] == "Systems administrators"
    assert rows[0]["score"] == 0.625
    assert rows[0]["release_version"] == "2026-05"
