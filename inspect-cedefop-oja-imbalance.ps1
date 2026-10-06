$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.inspect_cedefop_oja_imbalance @args
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "OJA imbalance CSV is missing or its schema is not yet recognised. Follow the JSON diagnostic."
        exit 2
    }

    if ($Code -ne 0) {
        throw "Cedefop OJA imbalance inspection failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
