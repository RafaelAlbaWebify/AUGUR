$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run bootstrap-augur.ps1 or setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -m scripts.check_operability
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($Code -eq 0) {
    Write-Host ""
    Write-Host "AUGUR is fully operational." -ForegroundColor Green
    exit 0
}

if ($Code -eq 2) {
    Write-Warning "AUGUR is partially operational. Review blockers above."
    exit 2
}

throw "AUGUR evidence stores are empty or unusable."
