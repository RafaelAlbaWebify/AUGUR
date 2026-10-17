# Official-source reference database in CI

## Public repository policy
AUGUR intentionally remains public for free standard GitHub-hosted Actions minutes. Only data downloaded from public official statistics endpoints may be included in the reference artifact. No local operator DuckDB, SQLite, personal profiles, secrets or tokens must be committed or uploaded. Workflow artifacts in public repositories can be accessible to authorized repository participants and should be treated as **public**, not confidential. Storage/retention limits still apply.

## Reference DB design
`.github/workflows/private-official-reference.yml` dispatches a public-repository ephemeral runner. It executes ingestion regression checks, fetches genuine Eurostat 2025 employment (Y20-64) and unemployment (Y20-64, education TOTAL) for 31 defined pilot NUTS2 codes in ESP/IRL/PRT, rejects missing/duplicate/dimension-incompatible rows, and writes a separate reference DuckDB plus provenance/quality report. Artifacts expire after seven days. No source-control database commits, no production files, no credentials and no operator-local run required.

The reference dataset is a **reproducible provider snapshot**, not a byte-identical reproduction because official providers revise observations over time; returned source update metadata and retrieval timestamp are retained. The selected codes are pilot scope, not official full world coverage. Provider `d`/other flags remain visible and block automatically certifying ranking eligibility; NUTS boundary vintage is not certified from code membership.

## Next gates
1. Run workflow_dispatch on the public repository and inspect live output. Do not claim successful live-source CI until that run passes.
2. Compare source-vetted reference rows against a **sanitized** read-only operator export of production observations. Do not publish personal application data.
3. Expand from pilot employment/unemployment to actual monitored indicator contracts, full write-path transaction checks, and API rankings only after quality/vintage gates.
4. Pin provider source definitions and observation snapshots for stable regression tests; compare new retrievals against recorded baselines and report revisions instead of silently replacing expected values.
