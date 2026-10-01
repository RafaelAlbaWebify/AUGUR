from app.db.bootstrap import initialize_datastores
from app.ingestion.un_wpp import UNWPPAdapter


def main() -> int:
    initialize_datastores()

    adapter = UNWPPAdapter(timeout_seconds=120, max_retries=3)

    try:
        result = adapter.sync_country("ESP")
    finally:
        adapter.close()

    print()
    print("AUGUR UN WPP sync")
    print("Country:", result["country_iso3"])
    print("Vintage:", result["vintage"])
    print("Rows stored:", result["rows"])
    print("Observed:", result["observed"])
    print("Official forecasts:", result["official_forecasts"])
    print("Indicators:", ", ".join(result["indicators"]))
    print("Complete:", result["complete"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
