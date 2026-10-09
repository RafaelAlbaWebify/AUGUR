param(
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$Country
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment missing. Run bootstrap-augur.ps1 first."
}
$Arguments = @("-m", "scripts.export_geography_provenance", "--output", $Output)
if ($Country) { $Arguments += @("--country", $Country) }
Push-Location $Backend
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Geography provenance export failed." }
}
finally { Pop-Location }
