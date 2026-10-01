param(
    [string]$Path,
    [switch]$Seed,
    [string]$Version = "1.2.1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run setup first."
}

Push-Location (Join-Path $Root "backend")
try {
    if ($Seed) {
        & $Python -m scripts.import_esco --seed --version $Version
    }
    elseif ($Path) {
        & $Python -m scripts.import_esco $Path --version $Version
    }
    else {
        throw "Use -Seed or provide -Path <ESCO CSV package folder>."
    }

    if ($LASTEXITCODE -ne 0) {
        throw "ESCO import failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
