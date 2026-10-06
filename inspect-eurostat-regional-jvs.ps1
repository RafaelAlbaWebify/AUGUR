$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.inspect_eurostat_regional_jvs @args
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "Regional JVS dataset is unavailable or its schema/coverage is not yet sufficient. Review the JSON diagnostic."
        exit 2
    }

    if ($Code -ne 0) {
        throw "Eurostat regional JVS inspection failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
