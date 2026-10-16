# GR-2 pilot employment/unemployment reconciliation — 2026-10-16

**Evidence:** operator-supplied `AUGUR_GR2_EMPLOYMENT_VINTAGE.json` and `AUGUR_GR2_UNEMPLOYMENT_VINTAGE.json`. Files are not committed: counts and identifiers only.

## Results

- Each report includes **31** unique registered 2025 NUTS2 regional observations: Spain **19**, Portugal **9**, Ireland **3**. Code lists are identical in both reports.
- Each group has exactly **one stored record**, source `EUROSTAT`, unit `percent`; employment dataset `lfst_r_lfe2emprt`; unemployment `lfst_r_lfu3rt`.
- All 62 records report `source_updated_at=2026-09-10T23:00:00+0200`. A source update timestamp does not certify observation comparability.
- All registry `name` values were null in these exports. UX must retrieve authoritative names or clearly display geo codes, not invent names.
- The Portugal list includes `PT11`, `PT15`, `PT19`, `PT1A`, `PT1B`, `PT1C`, `PT1D`, `PT20`, `PT30`. These appear in the [legally consolidated NUTS 2024 classification](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02003R1059-20240101). Ireland's `IE04`, `IE05`, `IE06` agree with the [Irish statistics office](https://www.cso.ie/en/methods/informationnotefordatausersrevisiontotheirishnuts2andnuts3regions/).
- The existing `app.services.regional_evidence.REGIONAL_INDICATORS` defines **both** pilots as Eurostat **annual, age 20–64, sex total, unit percentage**: `freq=A, age=Y20-64, sex=T, unit=PC`. Regression tests now guard against silent divergence from `PILOT_CONTRACTS`. The [official employment dataset](https://ec.europa.eu/eurostat/databrowser/view/lfst_r_lfe2emprt/default/table?lang=en) supports that dimension-specific approach.

## Gate not yet satisfied

The exports do **not** contain the full original Eurostat observation dimension tuple, quality flags, or a verified boundary-vintage reference per observation. Matching official code membership + configured filters is **not proof** of the ingested observation's full provenance. The region rankings remain intentionally blocked; do not set `boundary_verified=True` based only on this report.

**Next engineering work:** retain source response dimensions and quality status in a provenance record for future ingestions (without destructive DB migration); obtain authoritative NUTS 2024 dataset vintage evidence and independently reproduce ranked values on the user's DB. Only then allow a supported cohort to pass the production verification gate.
