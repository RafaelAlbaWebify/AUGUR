from app.db.analytics import source_quality_summary
from app.db.bootstrap import initialize_datastores


def test_source_quality_query_supports_common_period_fields():
    initialize_datastores()
    rows = source_quality_summary("ESP")

    for row in rows:
        assert "common_period" in row
        assert "common_period_source_count" in row
        assert "disagreement_pct" in row
