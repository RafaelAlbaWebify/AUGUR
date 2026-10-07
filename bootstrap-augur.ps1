param(
    [string]$EscoPath,
    [switch]$SkipSetup,
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Action,
        [int[]]$AllowedExitCodes = @(0)
    )

    Write-Host ""
    Write-Host "== $Label ==" -ForegroundColor Cyan
    & $Action
    $Code = $LASTEXITCODE

    if ($AllowedExitCodes -notcontains $Code) {
        throw "$Label failed with exit code $Code."
    }

    return $Code
}

Write-Host "AUGUR FULL BOOTSTRAP"
Write-Host "===================="

if (-not $SkipSetup) {
    Invoke-Step "Install and validate application" {
        & (Join-Path $Root "setup-phase0.ps1")
    } | Out-Null
}

if (-not $SkipSync) {
    $SyncCode = Invoke-Step "Synchronize official country evidence" {
        & (Join-Path $Root "sync-core.ps1")
    } -AllowedExitCodes @(0, 2)

    if ($SyncCode -eq 2) {
        Write-Warning "Core synchronization completed with partial provider failures. Operability check will identify remaining gaps."
    }

    $SubnationalCode = Invoke-Step "Synchronize registered-country subnational evidence" {
        & (Join-Path $Root "sync-subnational.ps1")
    } -AllowedExitCodes @(0, 2)

    if ($SubnationalCode -eq 2) {
        Write-Warning "Subnational synchronization completed with incomplete regional coverage."
    }
}

$BackendPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$LocalEvidenceCode = Invoke-Step "Ensure required local evidence" {
    Push-Location (Join-Path $Root "backend")
    try {
        & $BackendPython -m scripts.ensure_local_evidence
    }
    finally {
        Pop-Location
    }
} -AllowedExitCodes @(0, 2)

if ($LocalEvidenceCode -eq 2) {
    Write-Warning "Some optional local evidence could not be repaired automatically."
}

if ($EscoPath) {
    $ResolvedEscoPath = (Resolve-Path $EscoPath).Path
    Invoke-Step "Import full ESCO dataset" {
        & (Join-Path $Root "import-esco.ps1") -Path $ResolvedEscoPath -Version "1.2.1"
    } | Out-Null
}
else {
    Write-Host ""
    Write-Warning "No full ESCO package was supplied."
    Invoke-Step "Load partial ESCO seed" {
        & (Join-Path $Root "import-esco.ps1") -Seed -Version "1.2.1"
    } | Out-Null

    Write-Host "Country analysis can still be operational, but CareerFit/TTV evidence remains partial with seed ESCO."
    Write-Host "Download ESCO v1.2.1 CSV (English classification) from the official ESCO portal,"
    Write-Host "extract it, then rerun:"
    Write-Host '  .\bootstrap-augur.ps1 -SkipSetup -SkipSync -EscoPath "C:\path\to\esco"'
}

Write-Host ""
Write-Host "== Final operability check ==" -ForegroundColor Cyan
& (Join-Path $Root "check-operability.ps1")
$OperabilityCode = $LASTEXITCODE

if ($OperabilityCode -eq 0) {
    Write-Host ""
    Write-Host "Bootstrap complete: AUGUR is ready." -ForegroundColor Green
    Write-Host "Run:"
    Write-Host "  .\start-augur.ps1"
    exit 0
}

Write-Host ""
Write-Warning "Bootstrap completed, but AUGUR is not yet fully operational."
Write-Host "Resolve the blockers printed above and rerun .\check-operability.ps1."
exit $OperabilityCode
