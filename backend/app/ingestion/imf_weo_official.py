"""Official WEO October 2026 XLSX parser, independent of blocked DataMapper.

Source metadata decides the latest actual year for each country/series.
No database writes or implicit latest-vintage substitution.
"""
from __future__ import annotations
import io
import math
from datetime import datetime, timezone
from openpyxl import load_workbook

DATASET_VERSION = "IMF.RES:WEO(9.0.0)"
DATASET_ID = "WEO_OCTOBER_2026"
SOURCE_ID = "IMF"
METRICS = {
    "NGDP_RPCH": "real_gdp_growth",
    "PCPIPCH": "imf_inflation_average",
}
UNVERIFIED_UNIT_METRICS = {"LUR": "imf_unemployment_rate"}
REQUIRED = {"DATASET","COUNTRY.ID","INDICATOR.ID","FREQUENCY","UNIT",
            "LATEST_ACTUAL_ANNUAL_DATA","PUBLICATION_DATE"}


def normalize_official_weo(workbook: bytes, country_iso3s: set[str]) -> tuple[list[dict],dict]:
    if not workbook.startswith(b"PK"):
        raise ValueError("Official IMF WEO payload is not XLSX")
    book=load_workbook(io.BytesIO(workbook),read_only=True,data_only=True)
    try:
        if "Countries" not in book.sheetnames:
            raise ValueError("Missing IMF WEO Countries sheet")
        sheet=book["Countries"]
        iterator=sheet.iter_rows(values_only=True)
        header=next(iterator)
        columns={str(name):i for i,name in enumerate(header) if name is not None}
        if not REQUIRED <= columns.keys():
            raise ValueError("Missing IMF WEO metadata: "+str(sorted(REQUIRED-columns.keys())))
        years={int(name):idx for name,idx in columns.items() if name.isdigit() and len(name)==4}
        if not {2024,2025,2026} <= years.keys():
            raise ValueError("Official WEO year columns missing")
        wanted={str(code).upper() for code in country_iso3s}
        if any(len(code)!=3 or not code.isalpha() for code in wanted):
            raise ValueError("Country IDs must be ISO3-like")
        rows=[]
        seen=set()
        stats={"source_dataset":DATASET_VERSION,"vintage":"October 2026",
               "requested_countries":sorted(wanted),"accepted_series":METRICS,
               "blocked_indicator_ids":list(UNVERIFIED_UNIT_METRICS.values()),
               "blocked_reason":"LUR lacks explicit UNIT in verified official workbook metadata",
               "missing_latest_actual_series":0,"rows_by_type":{"observed":0,"official_forecast":0},
               "countries_with_data":[],"production_writes":0}
        covered=set()
        for entry in iterator:
            code=str(entry[columns["COUNTRY.ID"]] or "").upper()
            series=str(entry[columns["INDICATOR.ID"]] or "").upper()
            if code not in wanted or series not in METRICS:
                continue
            if str(entry[columns["DATASET"]] or "")!=DATASET_VERSION:
                raise ValueError(f"Unexpected IMF WEO dataset for {code}:{series}")
            if str(entry[columns["FREQUENCY"]] or "").lower()!="annual":
                raise ValueError(f"Unexpected IMF frequency for {code}:{series}")
            if str(entry[columns["UNIT"]] or "").lower()!="percent":
                raise ValueError(f"Unsupported IMF unit for {code}:{series}")
            cutoff=entry[columns["LATEST_ACTUAL_ANNUAL_DATA"]]
            if cutoff is None or isinstance(cutoff,bool) or not str(cutoff).isdigit() or int(cutoff)<1980:
                stats["missing_latest_actual_series"]+=1
                continue
            cutoff=int(cutoff)
            for year,column in years.items():
                raw=entry[column]
                if raw is None or raw=="" or raw=="n/a":
                    continue
                if isinstance(raw,bool) or not isinstance(raw,(float,int)) or not math.isfinite(raw):
                    raise ValueError(f"Invalid IMF WEO value for {code}:{series}:{year}")
                key=(code,series,year)
                if key in seen:
                    raise ValueError(f"Duplicate IMF WEO series: {key}")
                seen.add(key)
                kind="observed" if year<=cutoff else "official_forecast"
                rows.append({"country_iso3":code,"indicator_id":METRICS[series],
                             "period":year,"value":float(raw),"unit":"percent",
                             "source_id":SOURCE_ID,"dataset_id":DATASET_ID,
                             "observation_type":kind,"retrieved_at":datetime.now(timezone.utc),
                             "source_updated_at":str(entry[columns["PUBLICATION_DATE"]] or ""),
                             "source_observation_status":None,"source_decimal":None})
                stats["rows_by_type"][kind]+=1
                covered.add(code)
        stats["countries_with_data"]=sorted(covered)
        stats["observation_count"]=len(rows)
        return rows,stats
    finally:
        book.close()
