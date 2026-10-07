param(
    [string]$PdfPath = "",
    [string]$NormalizedOutput = "",
    [string]$ReviewOutput = "",
    [double]$Threshold = 0.84,
    [double]$MinMargin = 0.08
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

if (-not $NormalizedOutput) {
    $NormalizedOutput = Join-Path $Root "exports\eures_2025_annex_normalized.csv"
}
if (-not $ReviewOutput) {
    $ReviewOutput = Join-Path $Root "exports\eures_market_review.json"
}

$Arguments = @(
    "-m", "scripts.build_eures_market_evidence_from_annex",
    "--normalized-output", $NormalizedOutput,
    "--review-output", $ReviewOutput,
    "--threshold", "$Threshold",
    "--min-margin", "$MinMargin"
)

if ($PdfPath) {
    $Arguments += @("--pdf", (Resolve-Path $PdfPath).Path)
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
    Write-Host "ELA Annex extraction and ESCO review are fully resolved." -ForegroundColor Green
    exit 0
}

if ($Code -eq 2) {
    Write-Warning "ELA Annex review needs attention. Inspect exports\eures_2025_annex_extraction.json and exports\eures_market_review.json. Production evidence was not changed."
    exit 2
}

throw "ELA Annex review failed with exit code $Code."
