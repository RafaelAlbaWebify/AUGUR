# Official-source reference database in CI

## Security prerequisite
GitHub API reported AUGUR **public** on 2026-10-17. The new workflow is intentionally disabled until the repository is made **private** by its owner in GitHub Settings → General → Danger Zone → Change repository visibility. The GitHub connector does not have repository administration privileges. Verify third-party integrations, forks and collaborator access before changing visibility. Past public clones may survive the change: privacy is not retroactive.

Never commit, upload or attach an operator's SQLite profiles, live DuckDB, secrets, tokens or unreduced application state to the source tree. Repository privacy is not an alternative to data minimization.

## Reference DB design
`.github/workflows/private-official-reference.yml` dispatches a private-only ephemeral runner. It executes ingestion regression checks, fetches genuine Eurostat 2025 employment (Y20-64) and unemployment (Y20-64, education TOTAL) for 31 defined pilot NUTS2 codes in ESP/IRL/PRT, rejects missing/duplicate/dimension-incompatible rows, and writes a separate reference DuckDB plus provenance/quality report. Artifacts expire after seven days. No source-control database commits, no production files, no credentials and no operator-local run required.

The reference dataset is a **reproducible provider snapshot**, not a byte-identical reproduction because official providers revise observations over time; returned source update metadata and retrieval timestamp are retained. The selected codes are pilot scope, not official full world coverage. Provider `d`/other flags remain visible and block automatically certifying ranking eligibility; NUTS boundary vintage is not certified from code membership.

## Next gates
1. Make repository private, confirm API privacy state, then manually dispatch workflow and inspect live output. Do not claim successful live-source CI until that run passes.
2. Compare source-vetted reference rows against a **sanitized** read-only operator export of production observations. Do not publish personal application data.
3. Expand from pilot employment/unemployment to actual monitored indicator contracts, full write-path transaction checks, and API rankings only after quality/vintage gates.
4. Pin provider source definitions and observation snapshots for stable regression tests; compare new retrievals against recorded baselines and report revisions instead of silently replacing expected values.
