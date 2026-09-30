$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "AUGUR Phase 0 setup"
Write-Host "==================="

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found in PATH."
}

Write-Host ""
Write-Host "[1/4] Creating Python virtual environment..."
if (-not (Test-Path (Join-Path $Backend ".venv"))) {
    python -m venv (Join-Path $Backend ".venv")
}

$Python = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host "[2/4] Installing backend dependencies..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

Write-Host "[3/4] Installing frontend dependencies..."
Push-Location $Frontend
try {
    npm install
    npm run build
}
finally {
    Pop-Location
}

Write-Host "[4/4] Running backend tests..."
Push-Location $Backend
try {
    & $Python -m pytest
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Phase 0 setup complete."
Write-Host "Run:"
Write-Host "  .\start-augur.ps1"
