param(
    [string]$EscoPath,
    [string]$StasPath,
    [string]$OjaPath,
    [switch]$SkipSync,
    [switch]$GlobalBaseline
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
    if ($GlobalBaseline) {
        $GlobalCode = Invoke-Step "Synchronize global baseline country evidence" {
            & (Join-Path $Root "sync-global-baseline.ps1")
        } -AllowedExitCodes @(0, 2)

        if ($GlobalCode -eq 2) {
            Write-Warning "Global baseline refresh completed with no analyzable countries."
        }
    }

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

    $EeaHealthCode = Invoke-Step "Synchronize EEA regional PM2.5 health burden" {
        Push-Location (Join-Path $Root "backend")
        try {
            & $BackendPython -m scripts.sync_eea_health_burden
        }
        finally {
            Pop-Location
        }
    } -AllowedExitCodes @(0, 2)

    if ($EeaHealthCode -eq 2) {
        Write-Warning "EEA regional environmental-health evidence is currently unavailable."
    }

    $OecdRegionalCode = Invoke-Step "Synchronize OECD non-EU regional demographic evidence" {
        Push-Location (Join-Path $Root "backend")
        try {
            & $BackendPython -m scripts.sync_oecd_regional
        }
        finally {
            Pop-Location
        }
    } -AllowedExitCodes @(0, 2)

    if ($OecdRegionalCode -eq 2) {
        Write-Warning "OECD regional demographic evidence is currently unavailable."
    }

    $OecdUrbanCode = Invoke-Step "Synchronize OECD non-EU urban density evidence" {
        Push-Location (Join-Path $Root "backend")
        try {
            & $BackendPython -m scripts.sync_oecd_fua
        }
        finally {
            Pop-Location
        }
    } -AllowedExitCodes @(0, 2)

    if ($OecdUrbanCode -eq 2) {
        Write-Warning "OECD FUA/city density evidence is currently unavailable."
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

if ($StasPath) {
    $ResolvedStasPath = (Resolve-Path $StasPath).Path
    Invoke-Step "Refresh Cedefop STAS dataset" {
        & (Join-Path $Root "import-cedefop-stas.ps1") --input $ResolvedStasPath
    } | Out-Null
}
else {
    Write-Host ""
    Write-Host "Cedefop STAS dataset left unchanged."
    Write-Host "Use -StasPath only when you have downloaded a newer official STAS workbook."
}

if ($OjaPath) {
    $ResolvedOjaPath = (Resolve-Path $OjaPath).Path
    Invoke-Step "Refresh Cedefop OJA imbalance dataset" {
        & (Join-Path $Root "import-cedefop-oja-imbalance.ps1") --input $ResolvedOjaPath
    } | Out-Null
}
else {
    Write-Host ""
    Write-Host "Cedefop OJA imbalance dataset left unchanged."
    Write-Host "Use -OjaPath only when you have downloaded a newer official OJA imbalance CSV."
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
    Write-Host "Review the blockers above. Manual-package datasets are changed only when their corresponding -EscoPath, -StasPath or -OjaPath parameter is supplied."
    exit 2
}

throw "Refresh completed but AUGUR evidence stores are empty or unusable."
