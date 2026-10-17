## PERSISTENT CODE AUDIT — 2026-10-17
- Canonical audit: `docs/audit/README.md`, machine inventory `docs/audit/inventory.json`, findings `docs/audit/findings.json`. Review progress is SHA-verified; a source file modified after audit becomes stale automatically. Current checkpoint 35/35 DB+ingestion modules (100% **code review**, defects remain) and 35/347 scoped source files (10.09%), 14069 reviewed lines and 283 definitions. B02 source review is complete; unresolved defects are tracked by finding IDs. Next code review block B03: API/services/models; first remediation candidates include registry upsert atomicity and repeated bootstrap geo metadata loss.
- Highest-priority unresolved audit risks: Eurostat specialized numeric and dimension checks, IMF legacy forecasting semantics, EEA city Parquet provenance, OECD source identity, source-key/namespace normalization. Rankings retain official vintage/quality/production reconciliation restrictions. No operator DB writes.
- Operational rule: before changing any code, inspect `docs/audit/inventory.json` reverse Python imports (`imported_by`) and findings for exact file SHA, then run affected tests; update findings and ensure bot inventory refresh is green after merge. Do not treat static module graph as a full dynamic runtime graph.

# AUGUR — Operating Context

## GUARDRAILS
- Local checkout policy: maintain ONE permanent repository folder per project (the canonical main working directory). Do not create another clone, worktree, or PR-specific folder unless strictly necessary AND explicitly approved by the user beforehand. Prefer branches and CI on GitHub for isolated development.
- Temporary checkout lifecycle: document its reason and path, preserve local data and uncommitted changes, and remove it promptly once its approved purpose ends. Verify no orphan folders/worktrees remain. Never force-remove, reset, or clean user data.
- Respond in concise, natural English; prioritize verified results, paths, actions and blockers.
- When the user's English could sound more natural, suggest a correction and explain it in one short paragraph.
- At the start of each chat, read this file; verify GitHub repository, branch, HEAD commit, open PRs and CI.
- "Continue" means execute NEXT, rather than only proposing it; investigate and implement autonomously.
- Ask only for essential missing inputs, high-risk decisions or explicit authorization.
- Separate implemented, locally tested, CI-pending, CI-passed, merged and real-data accepted states.
- Never invent functionality, evidence, country/source coverage, operability or completion percentages.
- Protect local DuckDB/SQLite, ESCO data, secrets, user profiles, backups and existing installations.
- Do not delete data, force-reset worktrees or switch dirty checkouts without approval.
- Routine PR merges are pre-authorized when CI succeeds, GitHub reports mergeable, and scope is reviewed; merge without repeated permission requests. Obtain approval for destructive, security-sensitive, high-risk, or irreversible changes.
- Update STATE after meaningful work; include a direct PR link and live check status after each commit.
- Keep this file concise; replace obsolete status instead of accumulating history.
- Follow docs/operations/controlled-development-roadmap.md; EA reports every fixed weighted subphase.
- A subphase is 100% only with required tests, successful CI and a verified merge to the agreed branch.
- Keep real operational acceptance independent of merged development milestones.
- Preserve docs/PROJECT_STATE.md, ROADMAP.md, VALIDATION.md, DECISIONS.md and HANDOVER.md as detailed records.

## EVIDENCE-DRIVEN DELIVERY — 9/10 EFFICIENCY TARGET (adopted 2026-10-16)
- 9/10 is a measurable target, NOT an achieved score. Optimize accepted outcomes, not PR count, tool calls, messages or green CI alone.
- Before coding: audit the complete affected path (external source/contract -> request filters -> parser/normalizer -> DB/provenance -> service/API -> UI/consumer); examine current tests, observed failures and historical data. Identify shared root causes before patching symptoms.
- Define one bounded acceptance objective and written exit criteria first: exact scope, authorized modifications, actual evidence available, risks, tests, blockers and explicit STOP/GO conditions.
- Build a cohesive, reviewable work package covering related implementation, regression/integration tests, fixtures, safe migration/rollback design and documentation. Prefer 1–3 meaningful PRs per objective as a planning target, NOT a reason to bundle unrelated or risky changes.
- Do not merge a mere exploratory diagnostic as a product milestone if its unresolved findings can be investigated in the same branch. Use iterative CI inside the branch; merge after complete tests and review. Routine green, mergeable PRs may be merged under existing authorization.
- Prefer existing GitHub code, official data and isolated fixtures before requiring local PowerShell. Batch genuinely necessary local checks into ONE consolidated, read-only evidence package. Do not repeatedly ask the operator for near-identical reports.
- AUGUR GR-2 read-only Acceptance Runner (tools/acceptance.ps1) was implemented in PR #64. Extend it rather than treating it as missing. It should audit schema, metadata, dimensions, quality flags, full-cohort comparisons, missingness and reproducible ranking order; produce one timestamped versioned JSON report with failure reasons, source versions and explicit limits. Separate staging mode; never silently alter production.
- For any DuckDB/SQLite correction: first inventory and hash source, back up and test restore, prepare isolated staging copy, verify exact observation dimensions and policy/vintage, compare before/after and independently reproduce outputs. Production write/deletion/irreversible step requires explicit user approval. Never force-reset/clean user checkout or invent restored data.
- Quality gate: source semantic/contract unit tests -> integration/fixture tests -> full backend/frontend/ops CI -> independent real-data read-only audit -> local UX/operator acceptance where relevant. A CI pass is not statistical, source-vintage or operational acceptance.
- Report per objective: outcome, PR/commit/CI, real evidence, number of user-local executions, known blockers, next autonomous action. States: planned / implemented / CI-validated / real-evidence-validated / operator-accepted / blocked. No invented completion percentages.
- Track efficiency metrics per accepted objective (not per chat): elapsed lead time, PR count, user-local executions, avoidable rework loops, escaped source defects, success against acceptance contract. Targets: typically 1–2 local executions and 1–3 cohesive PRs, 100% required checks before merge, zero undocumented acceptance criteria, zero unverified operational claims, zero production writes without verified recovery. Exceptions must be justified.
- Handover and context: this augur.md is canonical concise entry point. Keep docs/PROJECT_STATE.md, docs/ARCHITECTURE or existing equivalent, docs/HANDOVER.md, docs/DECISIONS.md, docs/VALIDATION.md and roadmap synchronized rather than creating redundant competing source-of-truth files. A future docs/ai package is optional only if it reduces duplication. Replace stale NEXT/STATE, archive chronological PR details in Git/docs, and provide precise next-step checkpoint.
- Session boundary: user may close PC immediately after confirmed remote GitHub merge. Remote repository state persists; unsaved local edits and uncommitted local DB changes do not magically sync. Do not imply scheduled/background work. On next "continue", read this file, check HEAD/PRs, begin next accepted work package and request a local run only when the consolidated evidence harness is genuinely needed.

## CURRENT ACCEPTED GLOBAL SOURCE STATUS — 2026-10-17
- PR #86 merged as `844ad88`; full official October 2026 WEO global smoke [39031300201](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/39031300201) succeeded on public GitHub runners. World Bank 47,434 observations; UN WPP 130,464; IMF WEO 16,753 (14,627 observed, 2,126 official forecasts) for 178 countries; 194,651 total provider observations across 217 analyzable countries in 16.028 seconds. No operator production writes.
- World-level official WEO read-only source audit [39031119342](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/39031119342) verified 16,979/16,979 WEO observations in disposable DuckDB; the global World Bank catalogue intersects in 16,753. Missing latest-actual metadata for 35 series; LUR excluded because source UNIT is not explicit. IMF completeness remains partial; do not infer full coverage.
- OECD Australian population source-unit bug corrected by PR #85 (f7c36cf), validated by full live source smoke [39030260361](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/39030260361). `PS`=population and `PS_KM2`=density; never mix the two.
- UN WPP misses `CHI` (Channel Islands) from 217-country World Bank catalogue; this is explicit missingness, not zero or fabricated data. Regional rankings are **still blocked** on Eurostat source quality flags, NUTS boundary vintage, and unapproved historical production remediation.
- NEXT active package: automate versioned acceptance evidence artifacts and weekly source-change checks, with source-specific partial flags. Then handle remaining vintage/quality gate with official provider evidence and reversible operator-approved migration only. No overall release %.


## LIVE SOURCE BLOCKERS — 2026-10-17
- Live OECD AU203 2022 source dimensions independently verified in PR #85 read-only runner 39030025104: `POP/PS_KM2`=75.57 persons/km² and `POP/PS`=334683 persons, same TL3 code/year. Root cause: population normalizer previously ignored `UNIT_MEASURE`, then generic write contract correctly rejected conflicting rows. PR #85 filters population strictly to `PS` with unit multiplier 0 and regression tests; full live re-acceptance required after merge.
- IMF WEO official October 2026 dataset is available on data.imf.org, whose official SDMX 2.1/3.0 API replaces the unsupported DataMapper v1/v2 transport. **Critical:** IMF documentation identifies a per-country/series "Latest Actual Annual Data" metadata field, so AUGUR's global constant `FORECAST_START_YEAR=2026` is not sufficient to mark WEO observations versus estimates for every series/country. Do not migrate/relabel/publish WEO records until series-specific metadata and vintage are validated; avoid treating IMF 403 as proof of missing country data.
- Numerical ranking publication remains blocked on actual source quality, boundary vintage and local reconciliation. Operator DuckDB remains unchanged.

## CURRENT ACCEPTANCE CHECKPOINT — 2026-10-17 (verified from GitHub)
- Latest merged implementation: PR #79 (`b4cbee1`) changes national observation ingest to disk-backed batch staging to address observed DuckDB 12.4 GiB memory failure. PR CI passed; real baseline execution succeeded in run 39028369542 (217 analyzable countries, World Bank 47,434 rows, UN WPP 130,464 rows, IMF 0 rows/3 HTTP 403 failures). This accepts the memory-recovery behavior only; not complete IMF coverage or source reliability.
- PR #76 (`d8d2444`) verified disposable DuckDB rollback and DB/SQL/FastAPI consistency; live 62/62 Eurostat pilot source-to-app round-trip succeeded. 38 `d` and 2 `u` status flags remain visible, numerical rankings remain blocked. PR #77 (`0c157668`) added central-write inventory and recurring official-source-to-HTTP checks; PR #78 (`55822af6`) distinguishes stored unverified regional evidence from truly missing observations.
- PR #68–#75 merged: exact source dimensions, fail-closed input/batch validation, independent public official reference DuckDB build, national/regional transactional writes and canonical Eurostat regional age-cohort contracts. These do not prove other provider-specific source semantics or completeness.
- IMF blockage verified in 2026-10-17 global run: DataMapper v1/v2 HTTP 403 in all 3 series. PR #81 merged (1f048ab): bulk source `complete` now reports false on total fetch failure, regression-tested. New official WEO October 2026 exists at data.imf.org; any switch from pinned April 2026 vintage requires metadata/forecast semantics verification and live-source acceptance. Do not synthesize data or mark IMF accepted from World Bank/UN success.
- Historical operator DuckDB: 31/31 2025 regional employment records matched age Y15-64, not intended Y20-64. A 31-row isolated correction rehearsal was performed, with original local DB unchanged. Production changes need source SHA/pre-image, independent backup and restore rehearsal, verified quality/vintage, SQL/API reconciliation, then **explicit operator authorization**. No silent refresh.
- Ranking release gates: provider quality flags (`d`/`u`) require official dataset-specific policy; observation-to-NUTS boundary vintage is not independently established; historical production reconciliation and operator/browser acceptance remain pending. Keep numeric rankings blocked. No operability percentage.
- NEXT autonomous objective: investigate official IMF SDMX/CSV WEO transport and edition-specific observation/forecast metadata; retain blocked IMF until a live accepted ingestion succeeds. Prepare historical correction only in isolated staging; verify write/API read-through and update docs. Keep public GitHub Actions and protect local production data. Do not ask the operator to repeat completed GR-2 read-only/stage diagnostics.
- Efficiency: use complete affected-path audit and 1–3 cohesive PRs per bounded goal; no unsupported release claims or repeated user coordination.

## PROJECT
- Purpose: local-first country, regional and urban evidence, trajectories, comparisons and personal fit.
- Architecture: FastAPI/Python backend, DuckDB analytical evidence, SQLite app/profile state;
  React/TypeScript/Vite frontend; pytest, build and Playwright via GitHub Actions.
- Maintain separation of actual observations, official forecasts, analytical scenarios and personal fit.
- Repository: RafaelAlbaWebify/AUGUR; release target: main.
- Operating-context PR #45 merged to main; dashboard layout PR #46 merged to main.
- Rejected configurable/floating workspace: PR #44 closed unmerged; preserve proven main UI.
- Windows repository: ~/Documents/GitHub/AUGUR; start-augur.ps1, stop-augur.ps1,
  check-operability.ps1, refresh-augur.ps1, export-geography-provenance.ps1.
- Local frontend http://127.0.0.1:5190; backend http://127.0.0.1:8020.
- ESP/PRT/IRL are regression countries, not a global-coverage claim.

## STATE
- Main includes merged PR #45 and this operating-context file; current main HEAD not independently recorded here.
- PR #44 closed unmerged (rejected docking workspace); PR #46 merged (three-column dashboard).
- Previous PR #44 branch CI: 92/92 Playwright passed, but real visual acceptance FAILED;
  passing synthetic tests did not make the docking workspace usable.
- Implemented on main: national/regional evidence flows, provenance tooling, country UI,
  personal fit/TTV infrastructure and local start/stop tools; coverage remains source-dependent.
- Previously locally accepted: G2 ES/PT/IE data-layer reconciliation; wider release not accepted.
- Local operator last reported AUGUR operability partial: ttv_temporal_model blocker.
- Blockers: G3 real source/unit/period audit; genuine country journeys; external TTV holdout.
- PR #46 CI at 2116c8d: passed; merged to main as 030e802. Local visual acceptance of merged dashboard is still pending.
- Local Git recovery: HEAD and ORIG_HEAD repaired; backed-up staged changes archived.
  Single AUGUR worktree restored to main at dce469c; local pull of merged PR #46 still needed.
- PR #47 merged after green CI as cf13757: Country | Map | Changes ordering and larger evidence text.
- PR #47 Country Radar visually accepted by operator on 2026-10-16; preserve layout.
- Rankings and unified 1–3-location Compare planned in docs/GEOGRAPHIC_RANKINGS_ROADMAP.md; no ranking implementation or real-data validation claimed.
- GR-0 local evidence audit reviewed 2026-10-16: 2025 NUTS2 employment/unemployment stored for ESP19 + PRT9 + IRL3; 2024 Urban Audit city population ESP112 + PRT16. Statistical and boundary comparability pending. See docs/GR0_RANKING_READINESS_AUDIT.md.
- GR-1 initial fail-closed eligibility module + tests merged in PR #49 as 3282c5f; CI backend/frontend/ops green. Actual geographic-vintage certification and methodological acceptance not yet proven.
- GR-2 read-only regional ranking service and /api/rankings/regions merged in PR #50 as 7a133e4, with backend/frontend/ops CI green; API deliberately blocks ranking rows pending independent observation-vintage certification.
- PR #51 merged as 26d5731 with green backend/frontend/ops CI: exact-code read-only GR2 vintage exporter and source-grounded validation plan (docs/GR2_BOUNDARY_VINTAGE_ACCEPTANCE.md).
- GR-2 local evidence exports reviewed: 31 matching 2025 NUTS2 regions for each Eurostat employment/unemployment cohort (ESP19/PRT9/IRL3). PR #52 (15c6ba4) merged with CI green, testing exact configured source filters (annual, ages20-64, both sexes, percentages). See docs/GR2_PILOT_RECONCILIATION_20261016.md.
- PR #53 merged as 88581d8 (CI backend/frontend/ops passed): additive nullable `request_filters_json` on subnational observations, future regional Eurostat requests preserve exact requested dimensions. Historical rows remain unverified; not full response tuple/status/vintage certification. See docs/GR2_REQUEST_PROVENANCE_CAPTURE.md.
- PR #54 merged as 9f6cd99; backend/frontend/ops CI green: actual Eurostat provider-response dimensions + observation status captured in new nullable regional observation columns for future ingestions. Existing rows not retroactively verified.
- PR #55 merged as 489e334 (green backend/frontend/ops CI): GR2 read-only ranking now reports provider dimension mismatch, missing response metadata, geographic/time mismatch and status flags; all remain blocked absent independently verified vintage. Legacy fixtures supported with explicit missing metadata.
- PR #56 merged as dadeaa5 with green backend/frontend/ops CI: added read-only live Eurostat source-replay reconciler for both 2025 NUTS2 labour metrics, mismatch reasons and fixture tests; no DB writes or automatic boundary certification. See docs/GR2_LIVE_SOURCE_RECONCILIATION.md.
- PR #57 merged as 61c85a2 (backend/frontend/ops CI green): first local source replay found 0/62 accepted (29 apparent duplicates, 21 dimension/status review, 12 reported employment discrepancies). Fixed exact Eurostat response slice selection before duplicate detection. See docs/GR2_SOURCE_REPLAY_DIAGNOSTIC_20261016.md.
- PR #58 merged as 38dd97e with green backend/frontend/ops CI: V2 replay still 0/62 accepted (29 unemployment multiple exact-core provider rows; 33 numerical discrepancies across both metrics). Added diagnostic fields for full provider dimension tuple counts/extra dimension keys, and absolute value deltas without exporting raw values.
- PR #59 merged as 8e08793 (backend/frontend/ops CI green): V3 diagnosed 29 ambiguous unemployment rows caused by missing Eurostat isced11 education dimension. Explicitly query/validate isced11=TOTAL and update regression fixtures. Historical unemployment discrepancies PT20 0.3pp and PT30 0.1pp; employment all 31 regions differ by 4.5–7.6pp, unresolved. See docs/GR2_V3_ISCED_FINDING.md.
- PR #60 merged as 5fdffcf (backend/frontend/ops CI green): V4 replay proves 1/31 unemployment and 0/31 employment numerical matches; confirmed ingestion defect: requested Eurostat filters were never passed as dimension_values into normalizer and same-year multi-category rows could be silently reduced to an arbitrary first row. Fixed exact dimensions and duplicate-period fail-closed guard, with tests. See docs/GR2_V4_INGESTION_CAUSE.md.
- PR #61 merged as 831e6e1, green backend/frontend/ops CI: added read-only six-region historical sample comparing exact source values/dimensions and signed local-source deltas without modifying DuckDB. See docs/GR2_HISTORICAL_SAMPLE_DIAGNOSTIC.md.
- PR #62 merged as 6f32fb4, all CI green: 6-region 2025 historical sample confirmed employment stored values 5.1–5.8pp below latest Eurostat Y20-64 rates, while local source dimensions are unknown. Added safe read-only employment Y15-64 vs Y20-64 forensic sample with exact filters and regression tests. See docs/GR2_EMPLOYMENT_AGE_FORENSICS.md.
- PR #63 merged as f03007a (backend/frontend/ops CI green): 6/6 sampled 2025 employment values match Eurostat Y15-64 exactly, 0/6 match intended Y20-64. The read-only forensic now supports --all-registered for full ESP/IRL/PRT NUTS2 cohort, with tests and summary. See docs/GR2_EMPLOYMENT_FULL_COHORT_AUDIT.md.
- GR-2 2025 employment full-cohort local evidence received 2026-10-16: all 31 local stored employment values match Eurostat Y15-64 exactly; none match the intended Y20-64 cohort; 0 unresolved. Reference NEXT ACCEPTANCE OBJECTIVE and EVIDENCE-DRIVEN DELIVERY above.
- GR-2 consolidated acceptance run 2026-10-17: diagnostic_complete_not_certified; DB hash unchanged; employment local 31/31 match Y15-64 and 0/31 intended Y20-64; unemployment 1/31 numerical match, 29 discrepancies, 1 quality review. Report confirms historical source metadata null.
- PR #67 merged as b5dd4df (backend/frontend/ops CI green): first isolated staging trial stopped before copying DB: multi-geo fetch list was incorrectly passed to scalar exact-dimension normalizer, silently excluding all provider rows. Fixed normalizer config to filter scalar dimensions with per-row geo membership and completeness validation; two-code regression fixture and detailed missing geo diagnostic. Production DB remains unchanged.
- NEXT: retry isolated GR-2 staging after pulling main with AUGUR closed; upload staging JSON only. Assess flag/vintage/restore test and GR-3 local browser acceptance separately. No production writes or numeric ranking unlock.
- AFTER: G3 source/unit/period audit and real-data ESP/PRT/IRL country workflow validation.
- Progress begins at 0% merged for NEW roadmap deliverables until their acceptance is evidenced.
