"""Read-only official OECD source-dimension probe for conflicting population tuples."""
from __future__ import annotations
import csv
import io
import json
from collections import defaultdict
from app.ingestion.oecd_regional import OECDRegionalAdapter


def main() -> int:
    adapter = OECDRegionalAdapter()
    try:
        text = adapter.fetch_population(start_year=2022, end_year=2022)
    finally:
        adapter.close()
    groups = defaultdict(list)
    for record in csv.DictReader(io.StringIO(text)):
        if (record.get("COUNTRY","").upper() == "AUS"
            and record.get("REF_AREA","").upper() == "AU203"
            and record.get("MEASURE","").upper() == "POP"
            and record.get("AGE","").upper() in ("_T","TOTAL")
            and record.get("SEX","").upper() in ("_T","T","TOTAL")
            and record.get("TIME_PERIOD") == "2022"):
            groups[(record.get("REF_AREA"), record.get("TIME_PERIOD"))].append({
                key: value for key,value in record.items()
                if key not in {"TITLE", "OBS_COMMENT", "COMMENTS"}
            })
    print(json.dumps({"source": "OECD SDMX regional population", "matches": groups.get(("AU203","2022"), []),
                      "match_count":len(groups.get(("AU203","2022"), []))},indent=2))
    return 0 if groups.get(("AU203","2022")) else 2


if __name__=="__main__":
    raise SystemExit(main())
