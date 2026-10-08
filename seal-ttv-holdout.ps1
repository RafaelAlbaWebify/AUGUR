$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.seal_ttv_holdout
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($Code -ne 0) {
    throw "TTV holdout sealing failed with exit code $Code."
}
