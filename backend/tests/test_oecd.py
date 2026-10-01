from app.ingestion.oecd import OECDAdapter


def test_oecd_csv_normalization():
    csv_text = (
        "REF_AREA,FREQ,MEASURE,ACTIVITY,UNIT_MEASURE,PRICE_BASE,"
        "TRANSFORMATION,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
        "ESP,A,GDPHRS,_T,USD_PPP_H,LR,N,2023,58.25,A\n"
        "ESP,A,GDPHRS,_T,USD_PPP_H,LR,N,2024,59.10,A\n"
    )

    adapter = OECDAdapter(client=None)

    try:
        rows = adapter.normalize("ESP", csv_text)
    finally:
        adapter.close()

    assert len(rows) == 2
    assert rows[0]["country_iso3"] == "ESP"
    assert rows[0]["indicator_id"] == "gdp_per_hour_worked"
    assert rows[0]["period"] == 2023
    assert rows[0]["value"] == 58.25
    assert rows[0]["source_id"] == "OECD"
