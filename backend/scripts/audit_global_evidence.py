"""Audit any country's observations against declared geographic and source contracts."""
import argparse
import json
from pathlib import Path
from app.services.global_evidence_contract import EvidenceContract, coverage_matrix

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8"))
    contracts=[EvidenceContract(**c) for c in data["contracts"]]
    results=coverage_matrix(contracts,data["observations"],data["geographies"])
    report={"scope":"registered_geographies_only","results":results}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"Audited {len(results)} region/indicator combinations")

if __name__=="__main__":
    main()
