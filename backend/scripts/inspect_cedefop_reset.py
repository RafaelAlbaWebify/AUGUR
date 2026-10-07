from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.ingestion.cedefop_reset import (
    download_workbook,
    inspect_workbook,
    resolve_download_url,
)


def main() -> int:
    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 Cedefop RESET inspector"},
    ) as client:
        resolved = resolve_download_url(client)
        if resolved["status"] != "available":
            print(json.dumps({
                "dataset_id": "CEDEFOP_RESET",
                **resolved,
                "notes": [
                    "RESET discovery is informational; no data were written.",
                    "AUGUR does not guess a download URL when the official page does not expose one reproducibly.",
                ],
            }, indent=2, default=str))
            return 0

        path = settings.data_dir / "cache" / "cedefop_reset_2026-10.xlsx"
        download = download_workbook(
            client,
            path,
            resolved["download_url"],
        )

    result = inspect_workbook(path)
    result["resolver"] = resolved
    result["download"] = download
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
