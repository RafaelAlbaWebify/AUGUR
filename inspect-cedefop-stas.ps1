$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.inspect_cedefop_stas @args
    $Code = $LASTEXITCODE

    if ($Code -eq 2) {
        Write-Warning "STAS workbook downloaded but its schema is not yet fully recognised. Paste the JSON diagnostic into the AUGUR chat."
        exit 2
    }

    if ($Code -ne 0) {
        throw "Cedefop STAS inspection failed with exit code $Code."
    }
}
finally {
    Pop-Location
}
