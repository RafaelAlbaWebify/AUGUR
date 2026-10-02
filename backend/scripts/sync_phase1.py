from app.db.bootstrap import initialize_datastores
from app.ingestion.world_bank import WorldBankAdapter


def main() -> int:
    initialize_datastores()

    adapter = WorldBankAdapter(timeout_seconds=90, max_retries=3)

    try:
        result = adapter.sync_country("ESP")
    finally:
        adapter.close()

    print()
    print("AUGUR legacy World Bank diagnostic sync")
    print("Use scripts.sync_core for the current multi-provider workflow.")
    print("Country:", result["country_iso3"])
    print("Rows stored:", result["rows"])
    print("Indicators succeeded:", len(result["indicators"]))
    print("Indicators failed:", len(result["failures"]))
    print("Complete:", result["complete"])

    if result["failures"]:
        print()
        print("Failures:")
        for failure in result["failures"]:
            print(
                " -",
                failure["indicator_id"],
                failure["error_type"],
                failure["error"],
            )

    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
