"""No false purchasing-power conclusions from unusable price/income denominators."""
import pytest
from app.models.profile import PersonalProfileResponse
from app.services import financial_fit as module

@pytest.mark.parametrize("origin,target",[(0,100),(100,0),(float("nan"),100),(100,float("inf")),(True,100)])
def test_invalid_price_level_rejected_without_division(monkeypatch,origin,target):
    prices={"ESP":{"indicator_id":"household_price_level_index","value":origin,"period":2025,"source_id":"EUROSTAT"},
            "PRT":{"indicator_id":"household_price_level_index","value":target,"period":2025,"source_id":"EUROSTAT"}}
    monkeypatch.setattr(module,"_latest_price_level",lambda country:prices[country])
    profile=PersonalProfileResponse(profile_id="test",current_country="ESP",monthly_net_income=2400,remote_work=True)
    result=module.financial_fit(profile,"PRT")
    assert result["status"]=="insufficient_country_evidence"
    assert result["reason"]=="household_price_level_index_invalid"
    assert result["evidence_complete"] is False
    assert result["portable_income_analysis"] is None

def test_zero_portable_income_is_not_divided(monkeypatch):
    profile=PersonalProfileResponse(profile_id="test",current_country="ESP",monthly_net_income=0,remote_work=True)
    result=module.financial_fit(profile,"PRT")
    assert result["reason"]=="monthly_net_income_invalid"
    assert result["evidence_complete"] is False
