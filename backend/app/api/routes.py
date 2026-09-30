from fastapi import APIRouter

from app.core.config import settings
from app.db.bootstrap import datastore_status

router = APIRouter()


@router.get("/health")
def health():
    stores = datastore_status()
    ok = all(stores.values())
    return {
        "status": "ok" if ok else "degraded",
        "phase": 0,
        "version": "0.1.0-phase0",
        "datastores": stores,
        "paths": {
            "sqlite": str(settings.sqlite_path),
            "duckdb": str(settings.duckdb_path),
        },
    }
