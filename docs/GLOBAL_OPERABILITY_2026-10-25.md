# AUGUR global product operability — consolidated checkpoint (2026-10-25)

This is a **release-gate matrix**, not a claim that the entire application is usable. It consolidates existing project decisions; it supersedes neither source evidence nor the frozen TTV calibration protocol.

| Gate | Evidence as of 2026-10-25 | Status | Blocking next acceptance |
| --- | --- | --- | --- |
| National ESP/IRL compare | Operator `AUGUR_NATIONAL_ACCEPTANCE_FINAL.json`: 58/58 official-source agreement, no drift, real in-process HTTP API matches local DuckDB; frontend Playwright CI green | **ACCEPTED for this limited pair/data set** | An actual operator UI session remains outside the automated proof |
| Runtime/health | GitHub tests are green; `tools/augur11-release-smoke.ps1` exists | **NOT OPERATOR-ACCEPTED** | Start local app and run global GET-only smoke; review failures |
| Country analysis and trends | Routes, backend processing, CI and some existing regional/country inventories exist; user session release journey not recorded | **PARTIAL** | Actual ESP/IRL country journey including missing-data, source/period/unit labels |
| Regional NUTS and rankings | `docs/GR2_ACCEPTANCE_AND_REMEDIATION.md`: 31 registered 2025 NUTS2 employment observations are wrong age cohort for intended ranking; boundary vintage and quality flags unresolved | **BLOCKED for certified numerical leaderboards** | GISCO boundary correspondence, quality policy, restored-copy rehearsal and acceptance before write |
| Geographic/city | Geographic catalog/reconciliation documented, but source-specific live coverage and city observation age vary | **LIMITED** | Real stored records/periods and honest missing/legacy labels; cannot infer universe coverage from catalog |
| Profile, Personal Fit, Financial Fit | Code/routes and synthetic tests exist; real user profile journey not accepted | **NOT ACCEPTED** | Non-sensitive read-only operator journey, profile readiness and legal/financial dependency claims |
| Occupation/language demand | ESCO/EURES/Cedefop paths exist; Skills-OVATE detailed and live postings access gated | **LIMITED** | Verify exposed coverage labels, no fabricated share or inferred employer demand |
| TTV temporal forecasts | Backend bounded v1 exists; frozen acceptance requires prospective untouched external holdout | **BLOCKED for full predictive-ready release** | Legitimate external calibration, never synthetic substitution |
| Overall release | Many CI checks, source audit and data-layer acceptance, not all modules exercised on actual runtime | **NOT ACCEPTED** | Collect grouped runtime evidence and independently assess module workflows |

## Fastest next action
- With both frontend (default localhost:5190) and backend (default localhost:8020) already running, run **one** existing-repository command: `./tools/global-operability-audit.ps1`; default report path is **Downloads/AUGUR_GLOBAL_OPERABILITY.json**.
- This makes 21 HTTP GET requests against real local routes, checks selected shallow response contracts, and saves **only** statuses, duration, error type and aggregate module counters, with no private response bodies. It does not edit DuckDB or SQLite, start/sync services, claim source authenticity, or certify usability from HTTP 200.
- The operator report separates operational reachability from real-data acceptance. Fix any demonstrable availability/contract defects **in a single batch PR**, rerun only failed checks, and complete direct real-data UI acceptance for remaining functional gates.
- National 58/58 acceptance must not be extrapolated to regional ratings, rankings, forecasting or Personal Fit.
- Existing `tools/augur11-release-smoke.ps1` remains a narrower runtime regression check; this script adds breadth but does not replace its versioned release criteria.
