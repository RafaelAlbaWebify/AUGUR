param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("yes", "no")]
    [string]$Representative,

    [Parameter(Mandatory = $true)]
    [ValidateSet("yes", "no")]
    [string]$CohortCoverageAdequate,

    [string]$ReviewerLabel,
    [string]$Notes
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

$ArgsList = @(
    "-m", "scripts.review_ttv_holdout",
    "--representative", $Representative,
    "--cohort-coverage-adequate", $CohortCoverageAdequate
)

if ($ReviewerLabel) {
    $ArgsList += @("--reviewer-label", $ReviewerLabel)
}
if ($Notes) {
    $ArgsList += @("--notes", $Notes)
}

Push-Location $Backend
try {
    & $Python @ArgsList
    $Code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($Code -ne 0) {
    throw "TTV holdout review failed with exit code $Code."
}
