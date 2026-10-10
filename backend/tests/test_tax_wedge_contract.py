from app.services.tax_wedge_contract import tax_wedge_contract


def test_oecd_tax_wedge_contract_is_specific_and_does_not_make_up_values():
    c = tax_wedge_contract()
    assert c["measure"] == "AV_TW"
    assert c["household_type"] == "S_C0"
    assert c["earnings_of_principal"] == "AW100"
    assert c["unit_semantics"] == "percent_of_total_labour_cost"
    assert c["countries"] == ("ESP", "IRL", "PRT")
    assert "value" not in c
    assert "percent_of_total_labour_cost" != "percent_of_gross_salary"
