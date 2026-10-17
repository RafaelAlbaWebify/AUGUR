"""Independent fail-closed verification of a generated official-source reference DB."""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
import duckdb
from scripts.build_official_reference_db import CODES, INDICATORS, PERIOD
from app.services.regional_evidence import REGIONAL_INDICATORS

def audit(path: Path) -> dict:
    config = {row["indicator_id"]: row for row in REGIONAL_INDICATORS}
    expected = {(code, indicator) for codes in CODES.values() for code in codes for indicator in INDICATORS}
    con = duckdb.connect(str(path), read_only=True)
    try:
        rows = con.execute("""SELECT country_iso3, geo_code, indicator_id, period, value,
             unit, source_id, dataset_id, source_dimensions_json, source_status
             FROM reference_observations""").fetchall()
    finally:
        con.close()
    seen = set()
    flags = Counter()
    errors = []
    reverse = {code: country for country, codes in CODES.items() for code in codes}
    for country, geo, indicator, year, value, unit, source, dataset, raw_dims, status in rows:
        key = (geo, indicator)
        if key in seen: errors.append(f"duplicate:{geo}:{indicator}")
        seen.add(key)
        if key not in expected: errors.append(f"unexpected:{geo}:{indicator}")
        if country != reverse.get(geo): errors.append(f"country:{geo}")
        if indicator not in config:
            errors.append(f"indicator:{indicator}")
            continue
        contract = config[indicator]
        if year != PERIOD or source != "EUROSTAT" or dataset != contract["dataset_id"] or unit != contract["unit"]:
            errors.append(f"source_contract:{geo}:{indicator}")
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
            errors.append(f"invalid_value:{geo}:{indicator}")
        try:
            dims = json.loads(raw_dims)
        except (ValueError, TypeError):
            errors.append(f"invalid_dimensions:{geo}:{indicator}")
            continue
        required = {**contract["filters"], "geo":geo, "time":str(PERIOD)}
        if not isinstance(dims,dict) or any(str(dims.get(k)) != str(v) for k,v in required.items()):
            errors.append(f"dimension_mismatch:{geo}:{indicator}")
        if status: flags[(indicator,str(status))] += 1
    missing = sorted(expected - seen)
    if missing: errors.append(f"missing:{len(missing)}")
    if len(rows) != len(expected): errors.append(f"count:{len(rows)}:expected:{len(expected)}")
    report = {"status":"passed_not_quality_or_vintage_certified" if not errors else "failed",
              "rows":len(rows), "expected_rows":len(expected),
              "per_indicator":{i:sum(r[2] == i for r in rows) for i in INDICATORS},
              "flag_counts":{f"{i}:{flag}":n for (i,flag),n in sorted(flags.items())},
              "quality_certified":False,"boundary_vintage_certified":False,
              "errors":errors}
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",required=True,type=Path)
    parser.add_argument("--report",required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.db)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))
    if result["errors"]: raise SystemExit(2)

if __name__=="__main__":
    main()
