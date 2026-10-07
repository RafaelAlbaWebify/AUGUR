from __future__ import annotations

import argparse

from app.catalog import VALIDATION_COUNTRY_ISO3
from app.db.analytics import country_record
from app.db.bootstrap import initialize_datastores
from app.providers import PROVIDERS, providers_for_country


DEFAULT_COUNTRIES = list(VALIDATION_COUNTRY_ISO3)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize AUGUR core sources.")
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="ISO3 country codes. Defaults to the validation set; other countries are registered dynamically from World Bank metadata.",
    )
    args = parser.parse_args()

    countries = [value.upper() for value in args.countries]
    invalid = [code for code in countries if len(code) != 3 or not code.isalpha()]
    if invalid:
        raise SystemExit(
            f"Country codes must be ISO3-like alphabetic codes: {', '.join(invalid)}"
        )

    initialize_datastores()

    adapters = {
        provider.provider_id: provider.adapter_factory()
        for provider in PROVIDERS
    }
    shared = {}

    try:
        for provider in PROVIDERS:
            if provider.prepare is None:
                shared[provider.provider_id] = None
                continue

            print(f"Preparing shared payload for {provider.label}...")
            shared[provider.provider_id] = provider.prepare(
                adapters[provider.provider_id]
            )

        all_results = {}

        for country_iso3 in countries:
            print()
            print("=" * 72)
            print(f"AUGUR CORE SYNC · {country_iso3}")
            print("=" * 72)

            country = country_record(country_iso3)
            if country is None:
                print("Registering country from World Bank metadata...")
                country = adapters["WORLD_BANK"].ensure_country_registered(
                    country_iso3
                )
                print(
                    f"Registered {country['name']} "
                    f"({country.get('iso2') or '??'}/{country['iso3']})"
                )

            results = {}

            for provider in providers_for_country(country_iso3, country=country):
                print()
                print(f"[{provider.label}]")

                results[provider.provider_id] = provider.sync(
                    adapters[provider.provider_id],
                    country_iso3,
                    shared.get(provider.provider_id),
                )

            all_results[country_iso3] = results

    finally:
        for adapter in adapters.values():
            adapter.close()

    print()
    print("=" * 72)
    print("AUGUR CORE SYNC SUMMARY")
    print("=" * 72)

    complete = True

    for country_iso3, source_results in all_results.items():
        print(country_iso3)

        for source_id, result in source_results.items():
            source_complete = bool(result.get("complete", True))
            complete = complete and source_complete
            print(
                f"  {source_id:<12} rows={result.get('rows', 0):<5} "
                f"complete={source_complete}"
            )

    print()
    print("Complete:", complete)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
