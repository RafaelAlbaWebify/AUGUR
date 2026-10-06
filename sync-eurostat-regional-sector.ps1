$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.sync_eurostat_regional_sector @args
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "Regional Eurostat sector sync returned no usable rows."
        exit 2
    }
    if ($Code -ne 0) {
        throw "Regional Eurostat sector sync failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
