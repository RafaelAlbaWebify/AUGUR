# AUGUR — Operating Context

## GUARDRAILS
- Respond in concise, natural English; prioritize verified results, paths, actions and blockers.
- When the user's English could sound more natural, suggest a correction and explain it in one short paragraph.
- At the start of each chat, read this file; verify GitHub repository, branch, HEAD commit, open PRs and CI.
- "Continue" means execute NEXT, rather than only proposing it; investigate and implement autonomously.
- Ask only for essential missing inputs, high-risk decisions or explicit authorization.
- Separate implemented, locally tested, CI-pending, CI-passed, merged and real-data accepted states.
- Never invent functionality, evidence, country/source coverage, operability or completion percentages.
- Protect local DuckDB/SQLite, ESCO data, secrets, user profiles, backups and existing installations.
- Do not delete data, force-reset worktrees, switch a dirty checkout or merge important branches without approval.
- Update STATE after meaningful work; include a direct PR link and live check status after each commit.
- Keep this file concise; replace obsolete status instead of accumulating history.
- Follow docs/operations/controlled-development-roadmap.md; EA reports every fixed weighted subphase.
- A subphase is 100% only with required tests, successful CI and a verified merge to the agreed branch.
- Keep real operational acceptance independent of merged development milestones.
- Preserve docs/PROJECT_STATE.md, ROADMAP.md, VALIDATION.md, DECISIONS.md and HANDOVER.md as detailed records.

## PROJECT
- Purpose: local-first country, regional and urban evidence, trajectories, comparisons and personal fit.
- Architecture: FastAPI/Python backend, DuckDB analytical evidence, SQLite app/profile state;
  React/TypeScript/Vite frontend; pytest, build and Playwright via GitHub Actions.
- Maintain separation of actual observations, official forecasts, analytical scenarios and personal fit.
- Repository: RafaelAlbaWebify/AUGUR; release target: main.
- Working branch: docs/controlled-development-system-20261016; active documentation PR: #45 (draft; unmerged).
- Rejected configurable/floating workspace: PR #44 closed unmerged; preserve proven main UI.
- Windows repository: ~/Documents/GitHub/AUGUR; start-augur.ps1, stop-augur.ps1,
  check-operability.ps1, refresh-augur.ps1, export-geography-provenance.ps1.
- Local frontend http://127.0.0.1:5190; backend http://127.0.0.1:8020.
- ESP/PRT/IRL are regression countries, not a global-coverage claim.

## STATE
- Last verified main HEAD: b06b9b114ce7cf85d98e1a4f874e0e852554daa5 (PR #43 merged).
- At baseline: no open PRs; PR #44 closed without merge. No current main-head CI verified.
- Previous PR #44 branch CI: 92/92 Playwright passed, but real visual acceptance FAILED;
  passing synthetic tests did not make the docking workspace usable.
- Implemented on main: national/regional evidence flows, provenance tooling, country UI,
  personal fit/TTV infrastructure and local start/stop tools; coverage remains source-dependent.
- Previously locally accepted: G2 ES/PT/IE data-layer reconciliation; wider release not accepted.
- Local operator last reported AUGUR operability partial: ttv_temporal_model blocker.
- Blockers: G3 real source/unit/period audit; genuine country journeys; external TTV holdout.
- NEXT: check PR #45 CI and documentation acceptance; merge only with explicit approval.
- AFTER: conduct source/unit/period acceptance using existing G3 exporter, then real-data
  ESP/PRT/IRL country workflow validation, without reopening the rejected dock experiment.
- Progress begins at 0% merged for NEW roadmap deliverables until their acceptance is evidenced.
