"""Official WEO October 2026 XLSX parser, independent of blocked DataMapper.

Source metadata decides the latest actual year for each country/series.
No database writes or implicit latest-vintage substitution.
"""
from __future__ import annotations
import io
import math
from datetime import datetime, timezone
from openpyxl import load_workbook

OFFICIAL_WORKBOOK_URL = "https://data.imf.org/-/media/iData/External-Storage/Documents/0FA3DC49A04D446E9D69DBEB29979E1C/en/WEOOct2026all.xlsx"
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
               "missing_latest_actual_series":0,"missing_latest_actual_identifiers":[],"rows_by_type":{"observed":0,"official_forecast":0},
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
                stats["missing_latest_actual_identifiers"].append({"country_iso3":code,"indicator_id":METRICS[series]})
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
        stats["missing_latest_actual_identifiers"].sort(key=lambda item: (item["country_iso3"],item["indicator_id"]))
        stats["countries_with_data"]=sorted(covered)
        stats["observation_count"]=len(rows)
        return rows,stats
    finally:
        book.close()



class OfficialWEOAdapter:
    """Explicitly selected, metadata-constrained official WEO source adapter."""

    def __init__(self, client=None):
        import httpx
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=120,follow_redirects=True)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch_workbook(self) -> bytes:
        response=self.client.get(OFFICIAL_WORKBOOK_URL,headers={"User-Agent":"AUGUR-OfficialWEO/1.0"})
        response.raise_for_status()
        if not response.content.startswith(b"PK"):
            raise ValueError("Official WEO workbook did not return XLSX")
        return response.content

    def sync_countries(self, country_iso3s: list[str], *, workbook: bytes | None = None,
                       persist: bool = False) -> dict:
        payload=workbook if workbook is not None else self.fetch_workbook()
        rows,stats=normalize_official_weo(payload,set(country_iso3s))
        if not rows:
            raise ValueError("No eligible official IMF WEO rows")
        requested=set(stats["requested_countries"])
        covered=set(stats["countries_with_data"])
        missing_countries=sorted(requested-covered)
        # Accepted-metric coverage is distinct from deliberately blocked LUR scope.
        accepted_scope_complete=not missing_countries and not stats["missing_latest_actual_identifiers"]
        inserted=0
        if persist:
            from app.db.analytics import upsert_observations
            inserted=upsert_observations(rows)
        return {
            "countries":sorted({r["country_iso3"] for r in rows}),
            "country_count":len({r["country_iso3"] for r in rows}),
            "source":"IMF",
            "vintage":"October 2026",
            "rows":inserted if persist else len(rows),
            "persisted":persist,
            "complete":False,
            "accepted_scope_complete":accepted_scope_complete,
            "missing_requested_countries":missing_countries,
            "blocked_metric_ids":sorted(UNVERIFIED_UNIT_METRICS.values()),
            "failure_count":len(UNVERIFIED_UNIT_METRICS),
            "failures":[{"indicator_id":name,"reason":stats["blocked_reason"]}
                        for name in UNVERIFIED_UNIT_METRICS.values()],
            "series":[{"indicator_id":indicator,
                       "rows":sum(r["indicator_id"]==indicator for r in rows)}
                      for indicator in METRICS.values()],
            "source_contract":stats,
        }
