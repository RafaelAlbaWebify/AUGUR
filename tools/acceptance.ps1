param(
    [ValidateSet("GR2")][string]$Scope = "GR2",
    [ValidateSet("ReadOnly")][string]$Mode = "ReadOnly",
    [string]$Output = (Join-Path $HOME "Downloads\AUGUR_GR2_ACCEPTANCE.json")
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Existing backend virtual environment not found: $python" }
Push-Location (Join-Path $root "backend")
try {
    & $python -m scripts.accept_gr2 --output $Output
    if ($LASTEXITCODE -ne 0) { throw "GR2 acceptance diagnostic failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
Write-Host "Read-only acceptance report: $Output"
