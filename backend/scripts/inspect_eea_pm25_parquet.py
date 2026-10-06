from __future__ import annotations

import json
import tempfile
from pathlib import Path

import duckdb
import httpx

from app.ingestion.eea_air_quality_api import probe_verified_pm25_city


def _extract_urls(payload: dict) -> list[str]:
    raw = payload.get("raw_text") if isinstance(payload, dict) else None
    if not isinstance(raw, str):
        return []
    return [
        line.strip()
        for line in raw.lstrip("\ufeff").splitlines()[1:]
        if line.strip().startswith("http")
    ]


def main() -> int:
    probe = probe_verified_pm25_city("Oviedo", "ES", 2024)
    urls = _extract_urls(probe.get("urls") or {})
    if not urls:
        print(json.dumps({
            "status": "no_urls",
            "probe": probe,
        }, indent=2, default=str))
        return 2

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        response = client.get(urls[0])
        response.raise_for_status()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.parquet"
        path.write_bytes(response.content)
        escaped = str(path).replace("'", "''")
        con = duckdb.connect()
        try:
            description = con.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{escaped}')"
            ).fetchall()
            result = con.execute(
                f"SELECT * FROM read_parquet('{escaped}') LIMIT 5"
            )
            columns = [column[0] for column in result.description]
            sample_rows = [
                dict(zip(columns, row))
                for row in result.fetchall()
            ]
            row_count = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{escaped}')"
            ).fetchone()[0]
        finally:
            con.close()

    print(json.dumps({
        "status": "available",
        "city": "Oviedo",
        "year": 2024,
        "url_count": len(urls),
        "sample_url": urls[0],
        "download_bytes": len(response.content),
        "row_count": row_count,
        "columns": [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2],
            }
            for row in description
        ],
        "sample_rows": sample_rows,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
