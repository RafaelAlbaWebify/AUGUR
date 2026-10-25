# AUGUR v1.0 — B2 acceptance contract: Spain stay vs Ireland relocate
Frozen implementation supplement to [AUGUR v1.0 closure plan](AUGUR_V1_DEFINITIVE_CLOSURE_PLAN.md). Date: 2026-10-25.

## Goal and honest claim
Answer: **"Given the household's stated constraints, opportunities, and actual evidence, is it more suitable to remain in Spain or relocate to Ireland?"**
AUGUR must never claim a definitive winner when relocation costs, portable income, housing costs, personal eligibility or evidence are missing. The goal is **decision support**, not migration/legal/financial advice or a predictive TTV forecast.

## Current verified baseline
- B1 real operator report: frontend HTTP 200, backend healthy, ESP/IRL 29 latest indicators per country, 29 time series per country, 58/58 compare cells aligned with local snapshots, zero API errors. **B1 browser DOM/UX gate remains pending**.
- National source validation: 58/58 official current/historical source-vintage agreement.
- Existing implementation includes `app.services.personalized_compare`, `financial_fit`, `career_fit`, Legal/Language Fit, and `PersonalProfile` with age, citizenships, occupation, skills, language CEFR, household size, monthly net income, savings, remote-work indicator, and explicit preference weights.
- Existing model does **not** necessarily contain verified individual rent, moving expenses, pension portability/tax treatment, actual job offers, or visa determinations. Do not silently infer these from price indices or the public labour market.

## Decision evidence matrix (B2, MUST)
| Area | Required outcome | When absent |
| --- | --- | --- |
| Evidence-only country baseline | ESP vs IRL source, year, units, incompatible periods and provider visibility | Show missing, not zero |
| Preferences | Explicit 0–5 weights only; show covered/omitted dimensions and sensitivity where meaningful | No winner or implied utility |
| Career | Actual occupation/skills/language/qualification inputs, EURES/ESCO/Cedefop evidence provenance, scope limitations | Demand or employability unknown; not guaranteed jobs |
| Income | Distinguish earned income from portable income, and existing from hypothetical job offer | Cannot assume Spanish net salary or pension transfers to Ireland unchanged |
| Cost of living and housing | Eurostat price-level index only as relative aggregate context; housing burden not rent quote | Personal budget/affordability unresolved |
| Financial resilience | Savings/liquidity and household size where provided; never fabricate moving budget, Irish tax or pensions | Mark cost-to-move/household finances incomplete |
| Legal/language | Citizenship/eligibility rules require own evidence; CEFR shows reported ability, not proof of hire | Status unknown, not automatically eligible |
| TTV | Frozen prospective holdout missing | Predictive duration unavailable, must not appear scored |

## Two fixed scenarios — no user profile mutation
**S1: constrained move / unknown local offer.** Spain current; household 2; existing income known only as a disposable *synthetic fixture*, `remote_work=false`, no verified Ireland offer, no relocation/housing quote, missing explicit decision weights. **Expected:** cannot decide financially, unknown local salary, no personalized winner, sources displayed, requirements and missing inputs listed.

**S2: potential portable income and explicit preferences.** Same base, `remote_work=true` and disposable synthetic portable income, explicit 0–5 positive housing, career and healthcare preference weights, English CEFR if user provides it, availability of source-backed national evidence. **Expected:** compare purchasing-power direction without pretending a private rental price, avoid net-tax promises, show sensitivity and ranking limitations; explain that remote-work checkbox does not prove cross-border employer authorization or permanent salary portability. No definitive immigration advice.

**Optional real household application:** after synthetic acceptance, user can enter actual relevant values in local profile if they choose. Never put personal income/savings/profession in CI artifacts or shared logs. AUGUR should return a conditional recommendation only after actual *decision-critical* gaps are filled.

## B2 acceptance matrix (fail closed)
| ID | Test | PASS criterion |
| --- | --- | --- |
| B2-01 | Missing weights | Returns `weights_missing` or equivalent blocked/not ready; no winner |
| B2-02 | Explicit weights | Only declared supported weights influence personal ranking; contextual/duplicate series excluded |
| B2-03 | Relative purchasing power | Correct directional calculation from actual source price level, never advertises quoted rent |
| B2-04 | No presumed salary portability | `remote_work=false` and missing job evidence yield unknown local income |
| B2-05 | Legal/language | Missing citizenship/recognition/CEFR is surfaced, not assumed |
| B2-06 | Career | Occupation mapping and provenance explicit, access-gated postings never imply complete coverage |
| B2-07 | TTV | No calibrated move-time estimate or claimed readiness |
| B2-08 | Isolation | Disposable in-memory fixtures or isolated storage; user's real profile never overwritten |
| B2-09 | Real UI | On actual local frontend, country and personalized output appears with clear warnings and missing states |
| B2-10 | Regression | Backend/frontend/ops CI all green; no P0/P1 false claims |

## Work package (one B2 implementation batch)
1. **Audit** existing Personal/Financial/Legal/Language/Career Fit calculations and UI against B2-01..10. Reuse pytest and Playwright; do not implement a new recommendation engine.
2. **Test** both frozen disposable scenarios through isolated services; add tests only for uncovered critical misleading cases. Do not load or write operator's saved profile.
3. **Correct** proven P0/P1 errors only, grouped into **one coherent implementation PR**; document `NO_CODE_CHANGES` if none.
4. **Report** PASS/BLOCKED/LIMITED per gate, retaining B1 browser journey as pending until independently exercised.

## Completion trigger, time budget and release calendar
These are **planning estimates, not guarantees**:
- B2: **1–2 focused working days** including merged CI and targeted operator evidence, assuming no architectural blocking bug.
- B3 existing frozen geography/ranking-safety stabilization: **1–2 working days**, no new region data source / certified leaderboard requirement.
- Final A1–A6 acceptance, release notes, tag and operator sign-off: **1 working day**.
- Remaining from 2026-10-25: **~3–5 focused working days** if tests reveal no large P0/P1 defect and real UI acceptance can be completed; practical planning window **late October to early November 2026**, **not a promised delivery date**. A critical defect, unavailable external evidence, or unapproved local mutation stops the release rather than triggering unlimited new PRs.
- In terms of process, **B1 code is merged and its API portion accepted**; **B2 and B3 are the two remaining development batches**. One final acceptance follows. No fourth implementation batch without a new explicit release-scope decision.

## Stop / release decision
Ship as **AUGUR v1.0 LIMITED** only when all release A1–A6 mandatory gates pass, with no P0/P1 errors. Geo leaderboard and unvalidated predictive TTV may remain visibly unavailable by explicit v1 freeze. Mark unsupported legal/financial conclusions *unknown*. If this primary stay-vs-migrate scenario is fundamentally misleading or unusable, **block the release** instead of manufacturing a score.
