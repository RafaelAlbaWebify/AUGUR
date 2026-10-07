param(
    [string]$EscoPath,
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPython = Join-Path $Root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $BackendPython)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

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

Write-Host "AUGUR EVIDENCE REFRESH"
Write-Host "======================"

if (-not $SkipSync) {
    $SyncCode = Invoke-Step "Synchronize official country evidence" {
        & (Join-Path $Root "sync-core.ps1")
    } -AllowedExitCodes @(0, 2)

    if ($SyncCode -eq 2) {
        Write-Warning "Evidence refresh completed with partial provider failures."
        Write-Host "The operability check below will identify the remaining blockers."
    }

    $SubnationalCode = Invoke-Step "Synchronize registered-country subnational evidence" {
        & (Join-Path $Root "sync-subnational.ps1")
    } -AllowedExitCodes @(0, 2)

    if ($SubnationalCode -eq 2) {
        Write-Warning "Subnational refresh completed with incomplete regional coverage."
    }
}
else {
    Write-Host ""
    Write-Host "Country evidence sync skipped by request."
}

if (-not $SkipSync) {
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
}
else {
    Write-Host "Automatic evidence repair skipped because -SkipSync was supplied."
}

if ($EscoPath) {
    $ResolvedEscoPath = (Resolve-Path $EscoPath).Path
    Invoke-Step "Refresh full ESCO dataset" {
        & (Join-Path $Root "import-esco.ps1") -Path $ResolvedEscoPath -Version "1.2.1"
    } | Out-Null
}
else {
    Write-Host ""
    Write-Host "ESCO dataset left unchanged."
    Write-Host "Use -EscoPath only when you want to import or refresh the official ESCO package."
}

Write-Host ""
Write-Host "== Operability check ==" -ForegroundColor Cyan
& (Join-Path $Root "check-operability.ps1")
$OperabilityCode = $LASTEXITCODE

if ($OperabilityCode -eq 0) {
    Write-Host ""
    Write-Host "Refresh complete: AUGUR is fully operational." -ForegroundColor Green
    exit 0
}

if ($OperabilityCode -eq 2) {
    Write-Host ""
    Write-Warning "Refresh complete: AUGUR remains partially operational."
    Write-Host "Review the blockers above. No existing ESCO dataset was downgraded or replaced unless -EscoPath was supplied."
    exit 2
}

throw "Refresh completed but AUGUR evidence stores are empty or unusable."
