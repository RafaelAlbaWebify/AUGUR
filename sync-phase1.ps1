$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Script = Join-Path $Backend "scripts\sync_phase1.py"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

if (-not (Test-Path $Script)) {
    throw "Phase 1 sync script not found: $Script"
}

Push-Location $Backend
try {
    & $Python $Script

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
