from app.ingestion.un_wpp import UNWPPAdapter


def test_un_wpp_normalization_separates_estimates_and_projections():
    csv_text = (
        "ISO3_code,Variant,Time,TPopulation1July,TFR,MedianAgePop,LEx\n"
        "ESP,Medium,2023,48373.336,1.19,45.2,84.0\n"
        "ESP,Medium,2024,48797.875,1.18,45.5,84.1\n"
        "ESP,Medium,2030,50000.000,1.25,47.0,85.0\n"
        "PRT,Medium,2024,10500.000,1.40,46.0,82.5\n"
    )

    adapter = UNWPPAdapter(client=None)

    try:
        rows = adapter.normalize("ESP", csv_text)
    finally:
        adapter.close()

    assert len(rows) == 12

    by_key = {
        (row["indicator_id"], row["period"]): row
        for row in rows
    }

    assert by_key[("population_total", 2023)]["value"] == 48373336.0
    assert by_key[("population_total", 2023)]["observation_type"] == "observed"
    assert by_key[("population_total", 2024)]["observation_type"] == "official_forecast"
    assert by_key[("median_age", 2030)]["value"] == 47.0
    assert by_key[("life_expectancy", 2030)]["value"] == 85.0


def test_un_wpp_normalization_rejects_missing_spain_rows():
    csv_text = (
        "ISO3_code,Variant,Time,TPopulation1July,TFR,MedianAgePop,LEx\n"
        "PRT,Medium,2024,10500.000,1.40,46.0,82.5\n"
    )

    adapter = UNWPPAdapter(client=None)

    try:
        try:
            adapter.normalize("ESP", csv_text)
            raised = False
        except ValueError:
            raised = True
    finally:
        adapter.close()

    assert raised
