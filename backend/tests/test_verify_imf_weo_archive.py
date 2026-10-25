"""IMF archival verification stays fail-closed on units and vintage."""
import pytest
from scripts.verify_imf_weo_archive import compare_weo_archive


def rows():
    return [{"country_iso3": country, "indicator_id": indicator,
             "period": 2025, "dataset_id": "WEO_APRIL_2026",
             "unit": "percent", "source_id": "IMF", "value": value}
            for country in ("ESP", "IRL")
            for indicator, value in (("real_gdp_growth", 2.8),
                                     ("imf_inflation_average", 2.7),
                                     ("imf_unemployment_rate", 10.5))]


def test_missing_archived_file_is_not_accepted(tmp_path):
    with pytest.raises(FileNotFoundError):
        compare_weo_archive(rows(), tmp_path / "missing.xlsx")


def test_partial_imf_selection_rejected(tmp_path):
    with pytest.raises(ValueError, match="exactly six"):
        compare_weo_archive(rows()[:3], tmp_path / "not-needed.xlsx")
