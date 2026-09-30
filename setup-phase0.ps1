$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

function Assert-LastExitCode {
    param([string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

Write-Host "AUGUR setup"
Write-Host "==========="

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
    Assert-LastExitCode "Python virtual environment creation"
}

$Python = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host "[2/4] Installing backend dependencies..."
& $Python -m pip install --upgrade pip
Assert-LastExitCode "pip upgrade"

& $Python -m pip install -r (Join-Path $Backend "requirements.txt")
Assert-LastExitCode "backend dependency installation"

Write-Host "[3/4] Installing frontend dependencies..."
Push-Location $Frontend
try {
    npm install
    Assert-LastExitCode "npm install"

    npm run build
    Assert-LastExitCode "frontend build"
}
finally {
    Pop-Location
}

Write-Host "[4/4] Running backend tests..."
Push-Location $Backend
try {
    & $Python -m pytest
    Assert-LastExitCode "backend tests"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "AUGUR setup complete."
Write-Host "Run:"
Write-Host "  .\start-augur.ps1"
