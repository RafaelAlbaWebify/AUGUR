$ErrorActionPreference = "Stop"

Write-Warning "LEGACY DIAGNOSTIC: sync-phase1.ps1 only synchronizes World Bank data for ESP."
Write-Host "Use .\sync-core.ps1 for the current multi-provider AUGUR synchronization workflow."
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.sync_phase1

    if ($LASTEXITCODE -eq 2) {
        Write-Warning "Phase 1 sync completed with partial failures."
        exit 2
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Phase 1 sync failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
