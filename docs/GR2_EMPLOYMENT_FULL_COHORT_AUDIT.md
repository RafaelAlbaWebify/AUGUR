# GR-2 employment age-forensics — six-region result and expanded audit

The operator-provided `AUGUR_GR2_EMPLOYMENT_AGE_FORENSICS.json` confirms six exact numerical matches to Eurostat 2025 employment **Y15-64**, and zero matches to the intended **Y20-64** cohort. Each historic row lacks original request/response provenance; exact numerical resemblance is strong evidence but is not forensic proof of the original ingestion query. This aligns with the independently fixed normalization defect in PR #60.

The existing command remains a six-region sample. To examine **all locally registered 2025 ESP/IRL/PRT NUTS2 employment observations without database writes**, use:

```powershell
.\.venv\Scripts\python.exe -m scripts.inspect_ranking_employment_age --all-registered --output "$HOME\Downloads\AUGUR_GR2_EMPLOYMENT_ALL_REGIONS.json"
```

The tool discovers the local registered geography set read-only and compares the exact Y15-64 and Y20-64 source cohorts per geography. Summary counts include matches and unresolved requests; the output records public aggregate statistical values and quality flags. No rankings are approved and no database changes are made.

**Controlled remediation prerequisite:** review full-cohort output, establish authoritative NUTS vintage and quality-flag policy, back up DuckDB with independent restore test, and use a staged validation-and-approval process rather than running the general regional sync directly on historical records.
