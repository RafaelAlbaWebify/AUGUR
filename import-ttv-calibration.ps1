param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

$ResolvedPath = (Resolve-Path $Path).Path

Push-Location $Backend
try {
    & $Python -m scripts.import_ttv_calibration $ResolvedPath
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($Code -ne 0) {
    throw "TTV calibration import failed with exit code $Code."
}
