$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -c @'
from app.db.bootstrap import initialize_datastores
from app.ingestion.world_bank import WorldBankAdapter

initialize_datastores()

adapter = WorldBankAdapter(timeout_seconds=90, max_retries=3)

try:
    result = adapter.sync_country("ESP")
finally:
    adapter.close()

print()
print("AUGUR Phase 1 World Bank sync")
print("Country:", result["country_iso3"])
print("Rows stored:", result["rows"])
print("Indicators succeeded:", len(result["indicators"]))
print("Indicators failed:", len(result["failures"]))
print("Complete:", result["complete"])

if result["failures"]:
    print()
    print("Failures:")
    for failure in result["failures"]:
        print(
            " -",
            failure["indicator_id"],
            failure["error_type"],
            failure["error"],
        )
'@
}
finally {
    Pop-Location
}
