from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd import OECDAdapter


def main() -> int:
    initialize_datastores()

    adapter = OECDAdapter(timeout_seconds=90, max_retries=3)

    try:
        result = adapter.sync_country("ESP")
    finally:
        adapter.close()

    print()
    print("AUGUR OECD sync")
    print("Country:", result["country_iso3"])
    print("Rows stored:", result["rows"])
    print("Series succeeded:", result["series"])
    print("Complete:", result["complete"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
