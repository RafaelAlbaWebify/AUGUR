"""Archive CSV release selection regression tests."""
import csv
from scripts.verify_imf_weo_archive import compare_weo_archive

FIELDS = ["DATASET","SERIES_CODE","OBS_MEASURE","COUNTRY","INDICATOR","FREQUENCY","SCALE","UNIT","PUBLICATION_DATE","2025"]
CODES = {
    "real_gdp_growth": ("NGDP_RPCH", "Gross domestic product (GDP), Constant prices, Percent change", "Percent"),
    "imf_inflation_average": ("PCPIPCH", "All Items, Consumer price index (CPI), Period average, percent change", "Percent"),
    "imf_unemployment_rate": ("LUR", "Unemployment rate", ""),
}


def prepare(tmp_path, publish):
    stored = []
    file = tmp_path / "weo.csv"
    with file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for country in ("ESP", "IRL"):
            for indicator, (code, label, unit) in CODES.items():
                value = 2.8 if country == "ESP" else 4.7
                stored.append({"country_iso3": country, "indicator_id": indicator,
                               "period": 2025, "value": value, "source_id": "IMF",
                               "dataset_id": "WEO_APRIL_2026", "unit": "percent"})
                writer.writerow({"DATASET": "IMF.RES:WEO(9.0.0)", "SERIES_CODE": f"{country}.{code}.A",
                                 "OBS_MEASURE": "OBS_VALUE", "INDICATOR": label, "UNIT": unit,
                                 "PUBLICATION_DATE": publish, "2025": str(value)})
    return stored, file


def test_current_october_csv_is_never_mislabeled_april(tmp_path):
    rows, path = prepare(tmp_path, "2026-10-13T02:00:00Z")
    result = compare_weo_archive(rows, path)
    assert len(result) == 6
    assert all(x["status"] == "vintage_unverifiable" for x in result)


def test_april_csv_supported_for_six_observations(tmp_path):
    rows, path = prepare(tmp_path, "2026-04-14T00:00:00Z")
    result = compare_weo_archive(rows, path)
    assert len(result) == 6
    assert all(x["status"] == "match" for x in result)
