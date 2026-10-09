# AUGUR — Session Handover

Updated: 2026-10-09. **Read first on resumption, then revalidate live GitHub state.**

## Active task
Establish repository-anchored project-control protocol and stop context degradation; do **not** start new product work until baseline status has been published.

## Repository snapshot at creation
- Main includes PR #1 coverage + exporter, PR #2 geo provenance, PR #3 official GISCO audit.
- PR #4 `feature/compare-official-local-nuts` remains open **draft**, with green CI at inspection. Do not merge blindly; review source-contract validation and actual evidence requirements first.
- Project-control documents were prepared on `docs/project-control-system` (PR #5). Confirm whether merged before starting any new work; documentation-only changes may not trigger the path-filtered CI workflow.
- No new numeric completion percentage is justified.

## Known real evidence
- Local geography coverage JSON from user: 26 records; ES/IE/PT only; some historical NUTS2 overlap; OECD not represented in that export.
- Official GISCO catalog job: [37924620862](https://github.com/RafaelAlbaWebify/AUGUR/actions/runs/37924620862), ES NUTS2/3 = 19/59, IE 3/8, PT 9/26.
- Local per-code provenance JSON not yet available; comparing counts is insufficient.
- Existing detailed worklist: [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md).

## Next actions, in order
1. Confirm PR #5 merge status; if open, review the six documentation-only changed files and merge once valid. GitHub path-filtered CI may not trigger for docs-only changes.
2. Review PR #4 code and CI; add checks for malformed/missing/incomplete official catalog and duplicated local codes before merging.
3. Prefer independent GitHub-accessible official-source audits; if local codes are indispensable, request only the smallest necessary export.
4. Convert identified G2 mismatches into concrete accepted source-backed corrections; never delete historical codes on count disparity alone.
5. Start explicit G3 regional source/unit/period acceptance inventory; then C1/P1 product acceptance.
6. Maintain decision/evidence/handover docs with each milestone. Stop claiming “42% complete”.

## Standard workflow
**Start:** read PROJECT_STATE, ROADMAP, VALIDATION, DECISIONS, HANDOVER → inspect actual main, open PRs, CI, source limitations → choose highest-priority unblocked criterion.

**Build:** coherent milestone-sized implementation, tests, evidence verification, negative paths, documented assumptions → PR.

**Finish:** update current status, evidence, decisions, and exact next action in the same PR; merge after acceptance appropriate to milestone; leave external blockers visible.

**Never** repeat full repository recaps by speculation; use stable documents and live GitHub results.
