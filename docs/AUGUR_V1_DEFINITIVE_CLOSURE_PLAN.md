# AUGUR v1.0 — DEFINITIVE RELEASE FREEZE & CLOSURE PLAN
**Frozen on 2026-10-25.** This is the release scope and gate authority for v1.0. Do not silently expand or reinterpret it. The wider roadmap remains available for post-v1 work.

## Release identity, audience, and claims
- **AUGUR v1.0 = limited, local-first, evidence-based decision support** for comparing **Spain and Ireland**, consulting their country trends, examining available subnational evidence with source/year/coverage disclosures, and using bounded Personal/Financial/Legal/Career Fit evidence.
- **Portugal:** retain existing functionality with clear coverage labels; not part of the mandatory 58-observation source acceptance. No expanded Portugal validation is required to ship v1.0, but no misleading outputs or crashes are allowed in routes reachable through the shipped interface.
- v1.0 **does not** mean complete global coverage, verified regional numerical leaderboards, current transaction-level housing prices/rents, guaranteed job availability, or validated TTV duration prediction.
- A release's **100%** means **all mandatory v1 gates passed**, no P0/P1 defects, exclusions safely and visibly bounded, and a fixed release SHA/tag. It is not a percentage of source files, endpoints, features proposed, or universal AUGUR readiness.
- No fixed calendar deadline can responsibly be asserted before operator acceptance and external evidence; **development is capped at three focused batches plus one final acceptance**, not infinite rounds.

## Frozen scope — INCLUDED / LIMITED / EXCLUDED
| Area | Release decision | Observable criterion |
| --- | --- | --- |
| Desktop startup and local services | **MUST** | User starts app through existing shortcut/launcher; existing SQLite and DuckDB preserved; frontend 5190 and backend 8020 healthy; normal stop/restart and no critical error |
| Country Spain/Ireland comparison | **MUST** | 29 pairs, period/unit/source visible, missing/unequal-year disclosures; no spurious total winner; re-use already accepted 58/58 fixed-vintage source report; one true local browser journey |
| Country overview/trends | **MUST** | Genuine values and years/source, historical vs forecast/scenario distinction, honest Irish GDP/housing caveats; real country journey succeeds |
| Profile & Personal/Financial Fit | **MUST, bounded** | Two controlled non-sensitive scenarios, including missing/partial data; deterministic results, weights and limitations displayed, no unsupported personalized net-tax/rent/visa promises; do not expose or overwrite existing private profile |
| Legal, language and career evidence | **MUST, bounded** | Existing routes/UI function or visibly show insufficient evidence; ESCO/public demand coverage truthful, source scope visible; access-gated sources excluded |
| Geography/cities | **LIMITED** | Existing regional/city records only, marked by geography vintage, age, data scarcity and provider; no claim of comprehensive territory or contemporary city data |
| Regional numerical rankings | **LIMITED/BLOCKED** | `blocked_unverified_evidence` is valid until exact age cohort, observation-boundary vintage and provider quality flags independently accepted. The UI must not render unverified numbers as ranks. **Unlocking full leaderboards is not a release prerequisite** |
| TTV projected time/duration | **EXCLUDED from v1.0** | May show readiness/dependency status only, unmistakably not calibrated; no publishable predictive duration until prospective untouched holdout passes frozen protocol |
| Live postings, Skills-OVATE, commercial APIs | **EXCLUDED** | No provider access presumed; no synthetic/employer-share inference |
| Global onboarding, new indicators/providers, large redesign | **EXCLUDED** | Deferred to separate post-v1 roadmap; not considered blockers of this scope |
| Security/correctness and data safety | **MUST** | No data loss, unapproved writes, secret exposures, fabricated observations, critical crash or incorrect statistical assertions |

## Existing evidence: REUSE, DO NOT REPEAT
- 2026-10-25 operator `AUGUR_NATIONAL_ACCEPTANCE_FINAL.json`: ESP+IRL 58/58 source observations match, six IMF April 2026 archive cells validated, API alignment PASS, zero discrepancy; **national fixed selection accepted**. Not proof of other countries or of a browser journey.
- 2026-10-25 operator `AUGUR_GLOBAL_OPERABILITY(1).json`: 20/21 GET probes passed; the missing `indicator_id` for ranking probe was corrected in PR #151. Subsequent operator real GET to `/api/rankings/regions?indicator_id=regional_employment_rate&countries=ESP,IRL` returned `blocked_unverified_evidence`, `observed_rows=22`, `eligible_total=0`. **Service responds; leaderboard remains correctly blocked**.
- Earlier AUGUR11 release API consistent snapshot/trend/compare checks and CI exist. Keep explicit limits of synthetic tests, in-process HTTP and route-only probes.
- Known non-release constraints: regional NUTS2 age/boundary/quality gates (GR2), partial occupational-demand granularity, prospective TTV calibration.

## Three DEVELOPMENT BATCHES — hard maximum
### Batch 1 (B1): Start/release journey and national evidence UI
1. Run **one** live local desktop-start + ESP/IRL overview/compare/browser journey, not another shallow GET sweep. Confirm the already accepted observations appear with source/year/unit, mixed-year caveats, housing and Irish GDP qualifiers.
2. Check intended profile-free navigation and error/empty states. Preserve current layout unless a concrete P0/P1 error is proved.
3. **Change only confirmed** startup/browser, data-label, provenance or critical performance defects in one coherent PR. If none, record `NO_CODE_CHANGES`.
4. Acceptance artifact: redacted screenshots/observations, exact commit, runtime and datastore preservation check; do not store private profile content.
**Exit B1:** start, compare and country evidence journey PASS; no misleading material claim.

### Batch 2 (B2): Bounded personal-fit and employment acceptance
1. Validate **two controlled disposable/synthetic profiles** through actual service and UI flows: one with declared preferences and feasible data, one with missing weights/evidence. Never mutate operator's live personal profile to test.
2. Verify Personal Fit does not imply a winner absent valid weights; Financial Fit doesn't convert indices to personal rents/net income; Legal/Language/Career Fit disclose nationality, qualifications, language and provider coverage when unknown.
3. Verify any existing ESCO/career demand sources do not invent vacancy shares; TTV stays visibly experimental/not predictive.
4. Fix only P0/P1 inaccuracies/errors in **one coherent PR**; otherwise `NO_CODE_CHANGES`.
**Exit B2:** deterministic results or accurate bounded unknown states with user-visible limitations and no private-data writes.

### Batch 3 (B3): Geography/ranking safety, release stabilization
1. Inspect one genuine region/city route and ranking blocked-state through the UI. Cite period, geography vintage and missing source evidence; preserve current blocker for 22 observations until independently proven.
2. Verify no unapproved data migration/sync, accidental portfolio-wide claims or misleading rank/forecast. Check graceful restarts and meaningful empty/error states.
3. Revisit measured cold-start/career-fit latency **only if reproducible**, without optimization unrelated to release correctness.
4. Fix only P0/P1 issues in **one coherent PR**; otherwise `NO_CODE_CHANGES`.
**Exit B3:** regional/forecast limits properly surfaced, no unsafe numerical leaderboard; startup/restart and safety gate PASS.

## ONE FINAL ACCEPTANCE — no fourth development batch by default
| Gate | Required evidence | PASS |
| --- | --- | --- |
| A1 Local runtime | Desktop launch + restart, health, logs, preserve preexisting stores | No P0/P1, no unexpected data writes |
| A2 Compare/trends | Reuse 58/58 + real UI ESP/IRL user journey and source/year/missing states | Accurate values and qualified interpretation |
| A3 Personalized/financial/career | Two controlled cases, data/weights/missingness, relevant Legal/Language limitations | Correct result or explicit insufficiency; no false promises |
| A4 Geography & rankings | Existing regional/city UI, verified warning/blocked rank state | Unverified evidence never shown as certified leaderboard |
| A5 TTV boundary | UI/API explicitly distinguishes not-calibrated TTV | No predictive-ready claims |
| A6 Release engineering | CI all green on actual release SHA, no critical errors, final known-limitations note and evidence bundle in Downloads | Exact versioned SHA/tag and operator sign-off |

**Decision rule:** if all A1–A6 PASS and zero P0/P1, release **AUGUR v1.0 LIMITED** with scope/limitations. If a noncritical capability fails, disable/mark LIMITED clearly *without* misleading downstream outputs and record deviation. A critical blocker after B3 means **NO RELEASE / scope decision**, not an automatic B4. Never downgrade a P0/P1 to make the score look complete.

## Severity and change control
- **P0:** data loss, privacy/security exposure, dangerous unauthorized write, fabricated critical comparison, unrecoverable startup. Block release.
- **P1:** actual user journey fails, materially wrong personal/financial claims, source/year/unit mix-ups, unverified rank presented as valid, hidden TTV prediction. Block release.
- **P2:** minor slowness, polish, duplicate requests not materially affecting user decisions, optional incomplete sources with prominent limits. Record backlog; non-blocking.
- PR budget: at most **three implementation PRs**, one per batch, plus this planning-only freeze and optional final release metadata/tag. No splitting into tiny PRs; no feature requests after freeze. A batch with no changes uses no PR.
- User-held files and local database never overwritten without explicit approval and backup+restore rehearsal. Operator outputs go to `$HOME/Downloads`; repo artifacts only for required code/docs. CI and GitHub cannot establish personal-device database immutability on their own.
- Owner of release decision: operator. CI all green is necessary but not sufficient.

## Final deliverables
1. Versioned frozen scope and change ledger mapping B1–B3 to actual P0/P1 findings.
2. One redacted `AUGUR_V1_ACCEPTANCE.json` in Downloads with A1–A6 verdicts, limitations and evidence references (no profile PII).
3. Release notes stating **AUGUR v1.0 LIMITED**, supported geographies, certified observations, known exclusions and no predictive TTV.
4. Exact release commit SHA/tag and `MAINTENANCE_ONLY` status after operator acceptance.

**Stop rule:** Upon release, new sources, rankings unlock, detailed demand, TTV calibration, multi-country/world expansion and interface redesign are v1.1+ backlog, not blockers discovered mid-flight.
