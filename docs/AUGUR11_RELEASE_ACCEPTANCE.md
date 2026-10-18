# AUGUR 11 — Limited Release Acceptance (2026-10-18)

Status: **NOT ACCEPTED — real-data operator journey pending**.
Baseline main SHA: `04901c7479475079d277544f0a23d124447b9b59`.

## Outcome
One user can compare **Spain, Portugal and Ireland** with actual locally stored observations, understand relevant historical trends and employment/housing evidence where present, and identify which location merits further research. The product makes no unsupported claims of personalized suitability, current housing prices, comprehensive regional coverage, or validated time-to-value predictions.

## Freeze
No new providers, indicators, rankings, scoring engines, general refactoring or redesign before this bounded release. Only defects directly blocking the criteria below, correctness/security repairs and necessary narrowly scoped regression tests. The broader source audit is nonblocking unless a high-severity finding affects this journey.

## Five gates (currently not certified)
| Gate | Acceptance evidence | State |
| --- | --- | --- |
| R1 Runtime | Local app starts, existing SQLite/DuckDB preserved, health and operability outputs saved; startup/reload and API errors documented | NOT TESTED |
| R2 Compare | Real ESP/PRT/IRL Compare and Overview work end to end; source, period, unit, missing values and comparison methodology visible; one read-only independent observation check | NOT TESTED |
| R3 Provenance | Trends distinguished from observed values, scenarios/official forecasts separate, employment and housing limitations explicit, no incompatible geography/ranking or misleading global completeness claim | NOT TESTED |
| R4 User journey | Operator executes 10-minute task: choose ESP/PRT/IRL, compare unemployment/prosperity, inspect trend, assess employment and housing evidence, identify an investigation priority; screenshots/notes plus no critical errors | NOT TESTED |
| R5 Release qualification | Backend/frontend/ops CI at release commit; reproducible sanitized acceptance evidence; blockers classified; explicit operator sign-off | NOT TESTED |

A missing evidence layer can be marked **LIMITED** without blocking the release only if the user can clearly see it is unavailable and the proposed decision never relies on it. A false or misleading quantitative claim is a blocker.

## Evidence already present (NOT equivalent to acceptance)
- `frontend/tests/e2e/app.spec.ts` contains extensive mocked provider/API responses for ESP/PRT/IRL; it is not a live-store browser proof.
- `backend/tests/test_personalized_compare.py` exercises mathematical normalization using synthetic snapshots; it is not personal-fit real-data acceptance.
- `docs/VALIDATION.md` explicitly reports missing real-data frontend acceptance.
- `tools/acceptance.ps1` currently scopes to GR2; do not confuse it with this five-gate release.

## Cycle sequence and stop rule
**Cycle 1 — Baseline:** audit existing read-only tools and UI routes, define minimal operator evidence capture; do not request repeated exports or mutate user data. Deliver actual acceptance run or an exact minimal read-only command plus report format.

**Cycle 2 — Fix blockers only:** group directly observed critical defects in a coherent PR with regression tests. Reject unrelated feature requests.

**Cycle 3 — Re-run + decide:** repeat exactly the same criteria with authentic evidence and sign off PASS / LIMITED / FAIL for each gate. If a genuinely valuable journey still cannot be demonstrated, pause further development and reassess product scope and cost.

## Definition of done
Five gate decisions backed by evidence and a demonstrated useful journey; zero critical misleading-output defects; release caveats published. Not defined by PR count, code audit percentage, or abstract operability score.

## Safety
Read-only discovery, no local DuckDB/SQLite changes, no historical cohort rewrite, no unverified rankings unlock, no TTV model publication. Existing Country Radar UX preserved.

## First execution target
Use existing `check-operability.ps1`, current frontend, and read-only evidence/export routes. First inspect implementation and output safety. Gather local results once in a consolidated operator package only where GitHub cannot access the actual store.

## First operator HTTP evidence — 2026-10-18
Operator-supplied `AUGUR11_RELEASE_SMOKE.json` generated 2026-10-18T12:20:40Z at existing Windows checkout `C:\\Users\\ralba\\Documents\\GitHub\\AUGUR`. Results: 10/10 HTTP GET probes passed (frontend, /api/health, /api/operability, /api/countries, snapshots and overview-series for ESP, PRT, IRL); zero network failures. This certifies only endpoint **availability**, NOT response correctness, source provenance, nonempty observations, UI interaction, product acceptance, or that data did not change during application startup. Gate R1 = PARTIAL (startup and HTTP reachable, datastore immutability not established), R2–R5 = NOT CERTIFIED. Do not repeat this basic connectivity test absent a regression. Next evidence must inspect bounded, sanitized response content and a real-browser comparison journey, not merely HTTP 200.

## Real local API analytical consistency — 2026-10-18
Operator-supplied `AUGUR11_EVIDENCE.json` captured 2026-10-18T12:26:09Z: zero reported capture errors; `analysis_ready=true`, `status=partial`, blocker `ttv_temporal_model`. ESP/PRT/IRL each returned 29 snapshot indicators, 29 historical series and 229 history points (87 snapshots, 687 history points total). Checked all 87 snapshot latest tuples against their series' most recent period/value/unit/source; **87/87 matched**. Checked all 87 comparison cells against snapshots for period/value/source and indicator unit; **87/87 matched**. This supports **R2 partial / API consistency accepted**, not source-independent validity, frontend/browser UX or release acceptance.

Release-specific caveats: housing price/rent indices are NOT household affordability or actual rent amounts; housing overburden is population-level, NOT a personalized budget. Irish GDP/GDP-per-capita should not be used as a household welfare surrogate without qualification. Snapshot indicators span 2023–2026 reference periods and source updated/retrieved timestamps differ. IMF and Eurostat unemployment and IMF/WB/Eurostat inflation series are separately sourced constructs, not independent additive evidence. No source-website verification or actual UI inspection was performed. R3 remains unaccepted pending explicit UI caveat examination. TTV is intentionally out of scope, and no unvalidated ranking release is authorized.

Next: inspect rendered Compare/Overview on local browser with the accepted 2026-10-18 dataset; assess whether source, period and index caveats are intelligible and whether the user can finish the 3-country decision journey. Do NOT request another bulk JSON export or rerun connectivity. If a specific UI defect is seen, patch only that blocker with browser regression.
