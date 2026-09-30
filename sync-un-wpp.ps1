$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.sync_un_wpp

    if ($LASTEXITCODE -ne 0) {
        throw "UN WPP sync failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
