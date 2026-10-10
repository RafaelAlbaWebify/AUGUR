"""Versioned source-selection contract for OECD Taxing Wages comparisons.

No computed or estimated country values: contract only.
"""
from __future__ import annotations

TAX_WEDGE_CONTRACT = {
    "source_id": "OECD",
    "dataflow": "OECD.CTP.TPS,DSD_TAX_WAGES_COMP@DF_TW_COMP,2.1",
    "measure": "AV_TW",
    "household_type": "S_C0",
    "earnings_of_principal": "AW100",
    "earnings_of_spouse": "_Z",
    "frequency": "A",
    "unit_semantics": "percent_of_total_labour_cost",
    "scope": "single_person_no_children_at_100pct_of_country_average_wage",
    "countries": ("ESP", "IRL", "PRT"),
    "api_url": (
        "https://sdmx.oecd.org/public/rest/data/"
        "OECD.CTP.TPS,DSD_TAX_WAGES_COMP@DF_TW_COMP,2.1/"
        ".AV_TW..S_C0.AW100._Z.A"
    ),
    "data_explorer": (
        "https://data-explorer.oecd.org/vis?"
        "df%5Bag%5D=OECD.CTP.TPS&df%5Bid%5D="
        "DSD_TAX_WAGES_COMP%40DF_TW_COMP&df%5Bvs%5D=2.1"
    ),
    "warning": (
        "This is an OECD tax-wedge scenario, not the worker's actual "
        "income-tax rate, an average tax rate on gross salary, a net-pay "
        "calculator, or a local tax estimate. Country-specific average wages "
        "must not be treated as equal currency amounts."
    ),
}


def tax_wedge_contract() -> dict:
    return dict(TAX_WEDGE_CONTRACT)
