"""Housing evidence rejects booleans, NaN and infinities as numeric evidence."""
import pytest
from app.services.housing_affordability import housing_affordability_evidence

@pytest.mark.parametrize("value",[True,float("nan"),float("inf"),float("-inf")])
def test_invalid_housing_overburden_is_unavailable(value):
    result=housing_affordability_evidence([{"indicator_id":"regional_housing_cost_overburden_rate","status":"available","unit":"percent","value":value}])
    assert result["housing_cost_overburden"]["status"]=="unavailable"
    assert result["housing_cost_overburden"]["value_pct"] is None

@pytest.mark.parametrize("value",[True,float("nan"),float("inf"),float("-inf")])
def test_invalid_pps_income_is_unavailable(value):
    result=housing_affordability_evidence([{"indicator_id":"regional_disposable_income_pps_per_capita","status":"available","unit":"pps_per_person","value":value}])
    assert result["disposable_income_pps_per_capita"]["status"]=="unavailable"
    assert result["affordability_complete"] is False
