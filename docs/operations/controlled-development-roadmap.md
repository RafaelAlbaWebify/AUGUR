# AUGUR — Controlled Development Roadmap

Version: 1.0 (2026-10-16). Release target: `main`. Applies to *new controlled deliverables*;
it does not erase historical merged features or imply that existing implementation is absent.
Detailed requirements/evidence remain in ../PROJECT_STATE.md, ../ROADMAP.md,
../VALIDATION.md, ../DECISIONS.md and ../HANDOVER.md.

## Counting rules
- Phase weight is the sum of fixed subphase weights, always 100% per phase.
- Subphase merged completion is binary: **100%** only after its criteria are demonstrated,
  appropriate tests pass, GitHub CI is green, and the intended changes are verified merged
  to `main`; otherwise **0%**, with implementation/test/CI progress described separately.
- Phase progress = sum(subphase weight × subphase merged completion / 100).
- No partial or speculative percentages. Real-world operability is a **separate acceptance gate**.
- For documentation-only phases, automated checks may validate links/format/weights; a workflow
  that does not run is recorded as *CI not triggered*, never as passed.
- Record commit, PR, CI run, any real-store export and acceptance decision for each subphase.
- Numbering and weights are frozen at v1.0; revisions require a documented approved scope change.
- Historical G2 acceptance is retained in existing validation records, not re-scored retroactively.

## Phase 1 — Controlled delivery and safe baseline (0% merged)
| ID | Weight | Deliverable and objective evidence | Status |
| --- | ---: | --- | --- |
| 1.1 | 35% | Root `augur.md` referencing actual stable HEAD, constraints, NEXT; check file and PR diff | Implementing; unmerged |
| 1.2 | 35% | This roadmap with fixed weight arithmetic, merge-only gates and EA format; verify 100% totals | Implementing; unmerged |
| 1.3 | 30% | Baseline/rollback guard for preserved `main` UI and documentation links; PR review, required CI and explicit merge approval | Pending |

## Phase 2 — Real evidence provenance and coverage (0% merged)
| ID | Weight | Deliverable and objective evidence | Status |
| --- | ---: | --- | --- |
| 2.1 | 35% | G3 source/unit/period audit of existing local records using current exporter; sanitized evidence, no invented observations | Pending; some tooling exists |
| 2.2 | 35% | Reconcile observed geographic codes and boundary vintages against official registries; negative/historical cases tested | Pending; earlier G2 work exists |
| 2.3 | 30% | Country/regional/city coverage and missingness presented with accurate denominators and periods; tests plus real-data examples | Pending; partial implementation exists |

## Phase 3 — Country and personal-fit acceptance (0% merged)
| ID | Weight | Deliverable and objective evidence | Status |
| --- | ---: | --- | --- |
| 3.1 | 40% | ESP/PRT/IRL Country Radar/Map/Evidence end-to-end review on current `main` with authentic local data, screenshots and regressions | Pending; rejected PR #44 excluded |
| 3.2 | 30% | Financial/housing evidence and source provenance audited end-to-end; test units, years, missing values and disclaimers | Pending; modules exist |
| 3.3 | 30% | LegalFit/LanguageFit/CareerFit/FinancialFit realistic profile journeys with dependency and error-state tests | Pending; modules exist |

## Phase 4 — Operational qualification and external gates (0% merged)
| ID | Weight | Deliverable and objective evidence | Status |
| --- | ---: | --- | --- |
| 4.1 | 35% | Windows launch/stop/backup/non-destructive recovery and CI smoke; user-device evidence | Pending; scripts exist |
| 4.2 | 30% | Explicit release matrix with test CI, data freshness, security, UX and rollback; merged release evidence | Pending |
| 4.3 | 35% | TTV: prospective untouched representative holdout meets frozen criteria, reviewed and separately authorized model version; never synthetic substitute | External blocker |

## EA reporting and delivery procedure
For **every** subphase, print:
`Phase N.M → Name → Brief description and verified status → 0% or 100% complete → Weight: W% of phase total.`
Then `Total phase progress: Z%` for that phase. Report all four phases even if zero.
Never use CI green as a substitute for real-operator acceptance or external evidence.

For each NEXT: inspect actual branch/PR/CI, implement the smallest coherent milestone,
run available automated validation, record evidence in the relevant existing docs,
open a PR, and keep it unmerged until review/explicit approval. Avoid repeated
manual operator steps when the same validation is possible in GitHub.
