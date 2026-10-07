param(
    [string]$Input = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

$Arguments = @("-m", "scripts.import_cedefop_clssi")
if ($Input) {
    $Arguments += @("--input", (Resolve-Path $Input).Path)
}

Push-Location $Backend
try {
    & $Python @Arguments
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($Code -eq 0) {
    Write-Host ""
    Write-Host "Cedefop CLSSI import complete." -ForegroundColor Green
    exit 0
}

throw "Cedefop CLSSI import failed with exit code $Code."
