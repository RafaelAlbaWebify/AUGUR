$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.check_radar_evidence
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "One or more Country Radar evidence domains are still missing."
        exit 2
    }

    if ($Code -ne 0) {
        throw "Country Radar evidence check failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
