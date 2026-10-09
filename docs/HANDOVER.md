# AUGUR — Session Handover

Updated: 2026-10-09. **Read first on resumption, then revalidate live GitHub state.**

## Active task
G3 source/unit/period provenance audit is merged via PR #7 (`aa10370c`). This branch improves uninitialized-database diagnostics and tests. Project-control docs are merged; preserve distinction between code-level CI and actual local-data acceptance.

## Repository snapshot at creation
- PR #7 source/unit/period grouping and orphan-code report merged `aa10370c` after backend/frontend/ops CI passed; real-store acceptance remains pending.
- Main includes PR #1 coverage + exporter, PR #2 geo provenance, PR #3 official GISCO audit.
- PR #4 `feature/compare-official-local-nuts` merged as `ff3766e8`; exact-code comparison now rejects incomplete official catalogs and duplicate local codes. Actual private local matching is still unverified.
- Project-control documents were merged via PR #5 as `9ebe6484`. Documentation-only changes may not trigger path-filtered CI.
- No new numeric completion percentage is justified.

## Known real evidence
- Local geography coverage JSON from user: 26 records; ES/IE/PT only; some historical NUTS2 overlap; OECD not represented in that export.
- Official GISCO catalog job: [37924620862](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/37924620862), ES NUTS2/3 = 19/59, IE 3/8, PT 9/26.
- Local per-code provenance JSON not yet available; comparing counts is insufficient.
- Existing detailed worklist: [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md).

## Next actions, in order
1. Confirm PR #5 (project control) and PR #4 (strict code comparison) are merged; recheck GitHub live state before further changes.
2. Inspect actual local per-geography provenance when available; execute exact-code membership against GISCO 2024 and classify historical/unknown codes, rather than assuming count differences are corruptions.
3. Prefer independent GitHub-accessible official-source audits; if local codes are indispensable, request only the smallest necessary export.
4. Confirm versioned boundary membership before altering registration; protect historical observations, and never delete records based solely on count disparity.
5. Validate G3 regional source/unit/period audit: grouped by indicator, source, dataset, unit, temporal range; identify orphaned observation codes. Inspect CI and obtain real-data evidence separately, then continue C1/P1 acceptance.
6. Maintain decision/evidence/handover docs with each milestone. Stop claiming “42% complete”.

## Standard workflow
**Start:** read PROJECT_STATE, ROADMAP, VALIDATION, DECISIONS, HANDOVER → inspect actual main, open PRs, CI, source limitations → choose highest-priority unblocked criterion.

**Build:** coherent milestone-sized implementation, tests, evidence verification, negative paths, documented assumptions → PR.

**Finish:** update current status, evidence, decisions, and exact next action in the same PR; merge after acceptance appropriate to milestone; leave external blockers visible.

**Never** repeat full repository recaps by speculation; use stable documents and live GitHub results.
