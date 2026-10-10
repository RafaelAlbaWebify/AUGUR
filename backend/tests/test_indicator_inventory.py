from scripts.export_indicator_inventory import inventory
from app.catalog import INDICATORS


def test_inventory_matches_declarations_without_claiming_data_coverage():
    report = inventory()
    assert report["indicator_count"] == len(INDICATORS)
    assert report["scope"] == "declared_national_indicators_not_data_availability"
    assert all(row["indicator_id"] and row["dimension"] for row in report["items"])
