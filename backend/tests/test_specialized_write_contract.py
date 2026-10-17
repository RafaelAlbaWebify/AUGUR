"""Adversarial fixtures for specialized source-table write contracts."""
import pytest
from app.db.write_contract import validate_specialized_batch


def test_specialized_batch_accepts_valid_nullable_outlook():
    rows=[{"country_iso3":"ESP", "period":2025,"isco08":"25",
           "scenario":"BASE","source_id":"CEDEFOP","release_version":"2026",
           "employment_growth_pct":None,"employment_level_thousands":5.1}]
    validate_specialized_batch(rows,
        key_fields=("country_iso3","period","isco08","scenario","source_id","release_version"),
        optional_numeric_fields=("employment_growth_pct","employment_level_thousands"))


@pytest.mark.parametrize("broken,error",[
    ({"score":float("nan")},"Invalid specialized numeric field"),
    ({"score":True},"Invalid specialized numeric field"),
    ({"score":"7.5"},"Invalid specialized numeric field"),
    ({"isco08":""},"Missing specialized key"),
])
def test_specialized_rejects_corruption_before_database_access(broken,error):
    base={"isco08":"2","source_id":"CEDEFOP","release_version":"2026","score":7.0}
    with pytest.raises(ValueError,match=error):
        validate_specialized_batch([base,{**base,**broken}],
            key_fields=("isco08","source_id","release_version"),
            required_numeric_fields=("score",))


def test_specialized_key_is_case_insensitive_for_duplicate_detection():
    with pytest.raises(ValueError, match="Duplicate specialized write key"):
        validate_specialized_batch([
             {"isco08":"a2","source_id":"X","release_version":"V1","score":2.0},
             {"isco08":"A2","source_id":"x","release_version":"v1","score":3.0},
        ], key_fields=("isco08","source_id","release_version"),
           required_numeric_fields=("score",))
