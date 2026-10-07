param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPython = Join-Path $Root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $BackendPython)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

Push-Location (Join-Path $Root "backend")
try {
    & $BackendPython -m scripts.sync_global_baseline
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
