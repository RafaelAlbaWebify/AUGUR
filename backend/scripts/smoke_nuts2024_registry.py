"""Fail if the official GISCO 2024 NUTS2 source cannot be read as a registry."""
import json
import httpx
from app.ingestion.eurostat_nuts_registry import fetch_official_nuts2_codes, NUTS_2024_GEOJSON

def main():
    with httpx.Client(follow_redirects=True, headers={"User-Agent":"AUGUR/0.1"}) as client:
        codes=fetch_official_nuts2_codes(client)
    counts={prefix:sum(code.startswith(prefix) for code in codes)
            for prefix in ("ES","PT","IE","BG","FR")}
    print(json.dumps({"source":NUTS_2024_GEOJSON,"nuts2_count":len(codes),
                      "sample_country_counts":counts},indent=2))
    if not all(counts.values()):
        raise SystemExit("Missing pilot or Bulgarian/French geography from official NUTS2 registry")

if __name__=="__main__":
    main()
