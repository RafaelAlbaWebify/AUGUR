COUNTRIES = [
    {
        "iso2": "ES",
        "iso3": "ESP",
        "name": "Spain",
        "region": "Europe",
        "subregion": "Southern Europe",
        "currency": "EUR",
        "eu_member": True,
        "eurozone_member": True,
        "oecd_member": True,
    },
]

SOURCES = [
    {
        "source_id": "WORLD_BANK",
        "name": "World Bank",
        "organisation": "World Bank",
        "base_url": "https://api.worldbank.org/v2",
        "priority": 1,
    },
]

INDICATORS = [
    {
        "indicator_id": "population_total",
        "source_indicator": "SP.POP.TOTL",
        "name": "Population, total",
        "dimension": "demography",
        "unit": "persons",
        "higher_is_better": None,
    },
    {
        "indicator_id": "real_gdp",
        "source_indicator": "NY.GDP.MKTP.KD",
        "name": "GDP (constant 2015 US$)",
        "dimension": "productive_capacity",
        "unit": "constant_2015_usd",
        "higher_is_better": True,
    },
    {
        "indicator_id": "real_gdp_per_capita",
        "source_indicator": "NY.GDP.PCAP.KD",
        "name": "GDP per capita (constant 2015 US$)",
        "dimension": "prosperity",
        "unit": "constant_2015_usd_per_person",
        "higher_is_better": True,
    },
    {
        "indicator_id": "unemployment_rate",
        "source_indicator": "SL.UEM.TOTL.ZS",
        "name": "Unemployment, total (% of total labor force)",
        "dimension": "productive_capacity",
        "unit": "percent",
        "higher_is_better": False,
    },
    {
        "indicator_id": "employment_population_ratio",
        "source_indicator": "SL.EMP.TOTL.SP.ZS",
        "name": "Employment to population ratio, 15+, total (%)",
        "dimension": "productive_capacity",
        "unit": "percent",
        "higher_is_better": True,
    },
    {
        "indicator_id": "inflation_cpi",
        "source_indicator": "FP.CPI.TOTL.ZG",
        "name": "Inflation, consumer prices (annual %)",
        "dimension": "prosperity",
        "unit": "percent",
        "higher_is_better": None,
    },
    {
        "indicator_id": "fertility_rate",
        "source_indicator": "SP.DYN.TFRT.IN",
        "name": "Fertility rate, total (births per woman)",
        "dimension": "demography",
        "unit": "births_per_woman",
        "higher_is_better": None,
    },
    {
        "indicator_id": "population_65_plus_share",
        "source_indicator": "SP.POP.65UP.TO.ZS",
        "name": "Population ages 65 and above (% of total)",
        "dimension": "demography",
        "unit": "percent",
        "higher_is_better": None,
    },
    {
        "indicator_id": "net_migration",
        "source_indicator": "SM.POP.NETM",
        "name": "Net migration",
        "dimension": "demography",
        "unit": "persons",
        "higher_is_better": None,
    },
]
