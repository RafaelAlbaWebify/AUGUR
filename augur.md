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
- NEXT: run source-replay reconciliation against the operator's local DuckDB, resolve any code/value/response-dimension differences, independently confirm vintage, then unlock accepted numerical rankings and GR3 UX.
- AFTER: G3 source/unit/period audit and real-data ESP/PRT/IRL country workflow validation.
- Progress begins at 0% merged for NEW roadmap deliverables until their acceptance is evidenced.
