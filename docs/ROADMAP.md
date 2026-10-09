# AUGUR — Evidence-gated Roadmap

Updated: 2026-10-09. **No arbitrary completion percentages.** Each milestone is accepted only after criteria are evidenced. Detailed backlog: [AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md](AUGUR_REMAINING_IMPLEMENTATION_2026-10-07.md).

| ID | Outcome | Status | Acceptance criterion | Next action |
|---|---|---|---|---|
| R0 | Persistent project-control context | In progress | Five coordinating documents published on main and used on every consequential PR | Merge this documentation PR after review/CI |
| G1 | Observable regional coverage | Implemented + CI validated; local evidence partially inspected | Counts are actual stored distinct codes and years; export distinguishes absent data and catalog universe | Preserve real-export provenance and identify exact code mismatches |
| G2 | Official NUTS catalog comparison | Official catalog workflow CI validated; comparison PR #4 pending | Official 2024 code set compared *per country/level/code* against stored local provenance, with version mismatches classified; no automatic deletes | Review PR #4; obtain real comparison only if local provenance available |
| G3 | Source-backed regional/urban indicator completeness | Not accepted | Provider dataset-by-dataset source audit, observed periods, geo versions, units and missingness; UI displays limits | Review ES/PT/IE sparse indicators and OECD evidence separately |
| C1 | General country evidence / insight experience | Implemented in part; real acceptance unrecorded | Documented end-to-end country journeys with authentic synchronized data, error/empty states and consistent citations | Build focused acceptance matrix from existing UI audit |
| L1 | Occupational demand and skill/language evidence | Partial; externally constrained | Clear provider scope, actual occupation-level evidence, provenance, no fabricated skill demand; gated sources left explicitly gated | Review access-gated Skills-OVATE and posting vendor pilot only if defensible |
| P1 | Personal Fit + Financial Fit correctness | Partial; acceptance not established | Realistic profile journeys; legal/language/career/financial dependencies independently verified | Build acceptance scenarios and enumerate blockers |
| T1 | TTV external validation | Externally blocked | Representative prospective untouched holdout meets frozen criteria; version assigned *only if accepted* | Collect/review legitimate holdout; no synthetic substitution |
| O1 | Operability and release qualification | Not accepted | Explicit release-gate matrix, local runtime smoke + data/source audit + regression + blocking issues closed | Define release gates after G2/C1/P1 checks |

**Priority order:** G2 → G3 → C1/P1 → O1. T1 and access-restricted sources run independently; do not pretend their blockers can be solved by repository-only changes.

**Rules:** No invented observations; no forced coverage denominators; no conflation of geographies across boundary vintages; no declaring completion from CI alone. Prefer completing a milestone over accumulating one-file PRs.
