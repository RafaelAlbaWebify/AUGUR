from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.catalog import country_config
from app.db.analytics import country_record
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.imf import IMFAdapter
from app.ingestion.oecd import OECDAdapter
from app.ingestion.un_wpp import UNWPPAdapter
from app.ingestion.world_bank import WorldBankAdapter


AdapterFactory = Callable[[], Any]
SupportPredicate = Callable[[dict], bool]
PrepareHook = Callable[[Any], Any]
SyncHook = Callable[[Any, str, Any], dict]


@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    label: str
    adapter_factory: AdapterFactory
    supports: SupportPredicate
    sync: SyncHook
    prepare: PrepareHook | None = None


def _all_countries(_country: dict) -> bool:
    return True


def _eu_only(country: dict) -> bool:
    return bool(country.get("eu_member"))


def _oecd_only(country: dict) -> bool:
    return bool(country.get("oecd_member"))


def _standard_sync(adapter: Any, country_iso3: str, _shared: Any) -> dict:
    return adapter.sync_country(country_iso3)


def _prepare_un_wpp(adapter: UNWPPAdapter) -> str:
    return adapter.fetch_csv()


def _sync_un_wpp(
    adapter: UNWPPAdapter,
    country_iso3: str,
    shared: str | None,
) -> dict:
    return adapter.sync_country(country_iso3, csv_text=shared)


PROVIDERS = [
    ProviderSpec(
        provider_id="WORLD_BANK",
        label="World Bank",
        adapter_factory=lambda: WorldBankAdapter(timeout_seconds=90, max_retries=3),
        supports=_all_countries,
        sync=_standard_sync,
    ),
    ProviderSpec(
        provider_id="EUROSTAT",
        label="Eurostat",
        adapter_factory=lambda: EurostatAdapter(timeout_seconds=90, max_retries=3),
        supports=_eu_only,
        sync=_standard_sync,
    ),
    ProviderSpec(
        provider_id="OECD",
        label="OECD",
        adapter_factory=lambda: OECDAdapter(timeout_seconds=90, max_retries=3),
        supports=_oecd_only,
        sync=_standard_sync,
    ),
    ProviderSpec(
        provider_id="IMF",
        label="IMF",
        adapter_factory=lambda: IMFAdapter(timeout_seconds=90, max_retries=3),
        supports=_all_countries,
        sync=_standard_sync,
    ),
    ProviderSpec(
        provider_id="UN_WPP",
        label="UN WPP",
        adapter_factory=lambda: UNWPPAdapter(timeout_seconds=120, max_retries=3),
        supports=_all_countries,
        sync=_sync_un_wpp,
        prepare=_prepare_un_wpp,
    ),
]


PROVIDER_BY_ID = {provider.provider_id: provider for provider in PROVIDERS}


def providers_for_country(
    country_iso3: str,
    country: dict | None = None,
) -> list[ProviderSpec]:
    metadata = country
    if metadata is None:
        try:
            metadata = country_config(country_iso3)
        except ValueError:
            metadata = country_record(country_iso3)
    if metadata is None:
        raise ValueError(f"Country is not registered: {country_iso3}")

    return [
        provider
        for provider in PROVIDERS
        if provider.supports(metadata)
    ]
