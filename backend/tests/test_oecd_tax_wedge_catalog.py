from app.catalog import INDICATORS
from app.ingestion.oecd_tax_wedge import normalize_tax_wedge


def test_verified_tax_wedge_indicator_registered_with_correct_semantics():
    entries = [x for x in INDICATORS if x["indicator_id"] == "oecd_tax_wedge_average_wage"]
    assert len(entries) == 1
    assert entries[0]["unit"] == "percent_of_total_labour_cost"
    assert entries[0]["dimension"] == "fiscal"
    assert "not share of gross pay" in entries[0]["comparability_note"]
