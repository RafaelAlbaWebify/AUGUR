$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.sync_subnational @args

    if ($LASTEXITCODE -eq 2) {
        Write-Warning "AUGUR subnational sync completed with missing regional coverage."
        exit 2
    }

    if ($LASTEXITCODE -ne 0) {
        throw "AUGUR subnational sync failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
