param(
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$Country,
    [string]$System,
    [string]$Level
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment missing. Run bootstrap-augur.ps1 first."
}
$Arguments = @("-m", "scripts.export_geography_coverage", "--output", $Output)
if ($Country) { $Arguments += @("--country", $Country) }
if ($System) { $Arguments += @("--system", $System) }
if ($Level) { $Arguments += @("--level", $Level) }
Push-Location $Backend
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Geography coverage export failed." }
}
finally {
    Pop-Location
}
