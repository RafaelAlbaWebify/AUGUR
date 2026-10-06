$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.import_cedefop_stas @args
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "Cedefop STAS import completed without usable rows."
        exit 2
    }

    if ($Code -ne 0) {
        throw "Cedefop STAS import failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
