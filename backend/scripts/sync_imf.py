from app.db.bootstrap import initialize_datastores
from app.ingestion.imf import IMFAdapter


def main() -> int:
    initialize_datastores()

    adapter = IMFAdapter(timeout_seconds=90, max_retries=3)

    try:
        result = adapter.sync_spain()
    finally:
        adapter.close()

    print()
    print("AUGUR IMF sync")
    print("Country:", result["country_iso3"])
    print("Vintage:", result["vintage"])
    print("Rows stored:", result["rows"])
    print("Series succeeded:", len(result["series"]))
    print("Series failed:", len(result["failures"]))
    print("Complete:", result["complete"])

    if result["failures"]:
        print()
        print("Failures:")
        for failure in result["failures"]:
            print(
                " -",
                failure["indicator_id"],
                failure["source_indicator"],
                failure["error_type"],
                failure["error"],
            )

    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
