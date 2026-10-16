# GR-2 incremental Eurostat request provenance — 2026-10-16

New regional Eurostat ingestions now retain the **requested dimension filters** as JSON in an additive, nullable `subnational_observations.request_filters_json` column. Existing observation values, rows, and registry identity are unchanged. An existing database schema gains the nullable column at normal initialization, after any legacy geography-system migration. The change does not backfill unknown historical request dimensions.

**What is proven:** which `geo`, `freq`, `age`, `sex`, `unit` filters the AUGUR adapter requested when fetching newly imported observations. A regression test checks annual age 20–64 combined-sex percentage for the regional pilots.

**What is not proven:** the full Eurostat JSON-stat selected dimension tuple, per-observation quality/status flag, authoritative vintage of a historical region, and that a provider honored the requested filters without change. Request provenance must not be treated as independent provider observation validation.

**Next:** retain response-selected dimension tuple and raw quality flags, confirm official NUTS vintage of actual observations, and reconcile numerical rankings on local real data before lifting the `blocked_unverified_evidence` gate. Keep the Country Radar unchanged.
