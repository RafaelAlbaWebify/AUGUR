# AUGUR — Decision Register

Updated: 2026-10-09. Record architectural and workflow decisions, rejected alternatives and reversals; never rewrite historical rationale silently.

| ID | Decision | Rationale / alternative rejected | Consequence |
|---|---|---|---|
| ADR-001 | GitHub repository is the sole canonical project-control store. | Parallel Google Drive copy would drift from tested code and PRs. | Coordination docs live in `docs/` and are updated with material PRs. |
| ADR-002 | Distinguish **implementation**, **CI validation**, **actual local-data validation**, **product acceptance**, **external blockage**. | CI passing is not evidence that locally missing OECD/EU datasets exist. | No “fully operative” claims without source-backed acceptance. |
| ADR-003 | Retire unsupported global **42%** estimate. | No auditable denominator, weights or acceptance baseline existed. | Use milestone gate statuses; percentage needs approved scoring protocol. |
| ADR-004 | Never create invented provider metrics or missing-zero substitutions. | This would mislead country comparisons. | Test fixtures may be synthetic if isolated and identified; production observations must be authentic. |
| ADR-005 | Compare official 2024 NUTS code catalog against **native codes + levels + vintages**, not counts alone. | IE 5 vs 3 and PT 12 vs 9 may reflect historic boundary revisions; count difference is not proof of corrupted data. | Preserve raw records until a source-backed classification and migration decision. |
| ADR-006 | Private local DuckDB remains local; independent official-source verification runs in GitHub Actions. | CI and GitHub connectors cannot read user's Windows storage. | Minimize manual interactions; request local exports only for irreducibly local evidence. |
| ADR-007 | Preserve detailed original requirements and methodology documents; coordination files summarize and link them. | Replacing the existing roadmap or methodology risks losing decisions. | Historical specs remain primary for their domains. |

### Decision process
For any consequential change: identify problem → cite current evidence → state alternatives and trade-offs → decide → implement → run acceptance checks → link PR/commit/evidence → update project state/handover. Proposals awaiting verification must be labelled *proposed*, not accepted.

### 2026-10-17 — Validate before writing; make each supported evidence write atomic
**Decision:** treat public provider responses as untrusted until source-specific dimensions and a dataset-appropriate batch identity/numeric gate pass. In generic country/region and selected specialized evidence writers, wrap DuckDB replacements in a transaction with explicit rollback. Combine Eurostat regional labour/housing/health writes once after prevalidation; keep sector in a separately guarded transaction. **Rejected:** silent row-level partial writes, automatically treating NUTS current registry membership as historical vintage proof, or mutating the user's live DB without permission. **Trade-off:** compatibility tests and legitimate missing-measure rules differ by source; source-policy audit remains open. Implemented in PR #75 and proposed PR #76, acceptance dependent on CI/merge and external vintage/quality evidence.
