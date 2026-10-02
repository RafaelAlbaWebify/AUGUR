param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [string]$Output = "",

    [string]$EvidenceId = "eures_shortages_surpluses_2025_annex",

    [string]$RuleVersion = "EURES_SHORTAGES_SURPLUSES_2025_ANNEX",

    [int]$ReportYear = 2026,

    [int]$ConditionsYear = 2025,

    [string]$ReportUrl = "https://www.ela.europa.eu/sites/default/files/2026-06/annex-labour-shortages-report-ela-2025.pdf",

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

$ResolvedPath = (Resolve-Path $Path).Path

if (-not $Output) {
    $Output = Join-Path $Root "exports\eures_market_review.json"
}

$Arguments = @(
    "-m", "scripts.build_eures_market_evidence",
    $ResolvedPath,
    "--evidence-id", $EvidenceId,
    "--rule-version", $RuleVersion,
    "--report-year", "$ReportYear",
    "--conditions-year", "$ConditionsYear",
    "--report-url", $ReportUrl,
    "--output", $Output,
    "--threshold", "$Threshold",
    "--min-margin", "$MinMargin"
)

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
    Write-Host "EURES review artifact is fully resolved." -ForegroundColor Green
    exit 0
}

if ($Code -eq 2) {
    Write-Warning "EURES review artifact contains unresolved rows. Review the JSON output; production evidence was not changed."
    exit 2
}

throw "EURES evidence review failed with exit code $Code."
