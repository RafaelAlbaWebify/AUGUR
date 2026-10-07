$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$RunDir = Join-Path $Root ".run"
$LogDir = Join-Path $Root "logs"

$BackendPort = 8020
$FrontendPort = 5190
$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
$HealthUrl = "$BackendUrl/api/health"
$OperabilityUrl = "$BackendUrl/api/operability"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$BackendOut = Join-Path $LogDir "backend.out.log"
$BackendErr = Join-Path $LogDir "backend.err.log"
$FrontendOut = Join-Path $LogDir "frontend.out.log"
$FrontendErr = Join-Path $LogDir "frontend.err.log"

function Get-PortListeners {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $listeners = @()

    foreach ($connection in $connections) {
        if (-not $connection.OwningProcess) {
            continue
        }

        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" -ErrorAction SilentlyContinue

        $listeners += [pscustomobject]@{
            Port = $Port
            Pid = [int]$connection.OwningProcess
            Name = $process.Name
            CommandLine = $process.CommandLine
        }
    }

    return @($listeners | Sort-Object Pid -Unique)
}

function Test-AugurProcess {
    param($Listener)

    if ($null -eq $Listener -or -not $Listener.CommandLine) {
        return $false
    }

    return $Listener.CommandLine -like "*$Root*"
}

function Show-PortConflict {
    param(
        [int]$Port,
        [array]$Listeners
    )

    Write-Host ""
    Write-Host "Port $Port is already in use by a non-AUGUR process." -ForegroundColor Red

    foreach ($listener in $Listeners) {
        Write-Host "  PID $($listener.Pid) · $($listener.Name)"
        if ($listener.CommandLine) {
            Write-Host "  $($listener.CommandLine)"
        }
    }

    Write-Host ""
    Write-Host "AUGUR will not stop or replace that process." -ForegroundColor Yellow
}

function Show-BackendFailure {
    Write-Host ""
    Write-Host "AUGUR backend failed to become healthy." -ForegroundColor Red

    if (Test-Path $BackendErr) {
        Write-Host ""
        Write-Host "--- backend.err.log ---"
        Get-Content $BackendErr -Tail 80
    }

    if (Test-Path $BackendOut) {
        Write-Host ""
        Write-Host "--- backend.out.log ---"
        Get-Content $BackendOut -Tail 80
    }
}

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    throw "Frontend dependencies not found. Run setup-phase0.ps1 first."
}

Write-Host "Checking required local evidence..."
Push-Location $Backend
try {
    & $Python -m scripts.ensure_local_evidence
    $EvidenceCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($EvidenceCode -eq 2) {
    Write-Warning "Some optional local evidence could not be repaired automatically. AUGUR will start and report the remaining evidence gap."
}
elseif ($EvidenceCode -ne 0) {
    throw "Automatic local evidence check failed with exit code $EvidenceCode."
}

$BackendListeners = @(Get-PortListeners -Port $BackendPort)
$ReuseBackend = $false

if ($BackendListeners.Count -gt 0) {
    $ForeignBackendListeners = @($BackendListeners | Where-Object { -not (Test-AugurProcess $_) })

    if ($ForeignBackendListeners.Count -gt 0) {
        Show-PortConflict -Port $BackendPort -Listeners $ForeignBackendListeners
        throw "Cannot start AUGUR while port $BackendPort is owned by another project or process."
    }

    try {
        $ExistingHealth = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
        if ($ExistingHealth.status -eq "ok") {
            $ReuseBackend = $true
            Write-Host "AUGUR backend already running on $BackendPort. Reusing it." -ForegroundColor Green
        }
    }
    catch {
        # Listener belongs to AUGUR but does not answer health checks.
    }

    if (-not $ReuseBackend) {
        throw "A stale AUGUR backend is listening on port $BackendPort but is not healthy. Run .\stop-augur.ps1, then start AUGUR again."
    }
}

if (-not $ReuseBackend) {
    Remove-Item $BackendOut,$BackendErr -Force -ErrorAction SilentlyContinue

    Write-Host "Starting AUGUR backend on $BackendPort..."
    $BackendProcess = Start-Process `
        -FilePath $Python `
        -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","$BackendPort" `
        -WorkingDirectory $Backend `
        -RedirectStandardOutput $BackendOut `
        -RedirectStandardError $BackendErr `
        -PassThru

    $BackendProcess.Id | Set-Content (Join-Path $RunDir "backend.pid")

    Write-Host "Waiting for backend health..."
    $BackendHealthy = $false

    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        Start-Sleep -Milliseconds 500

        $BackendProcess.Refresh()

        if ($BackendProcess.HasExited) {
            Show-BackendFailure
            throw "AUGUR backend exited with code $($BackendProcess.ExitCode)."
        }

        try {
            $Health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
            if ($Health.status -eq "ok") {
                $BackendHealthy = $true
                break
            }
        }
        catch {
            # Backend may still be starting.
        }
    }

    if (-not $BackendHealthy) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
        Show-BackendFailure
        throw "AUGUR backend did not become healthy at $HealthUrl."
    }

    Write-Host "Backend healthy."
}

try {
    $Operability = Invoke-RestMethod -Uri $OperabilityUrl -TimeoutSec 5
    $OperabilityColor = if ($Operability.status -eq "ready") { "Green" } elseif ($Operability.status -eq "partial") { "Yellow" } else { "Red" }
    Write-Host "AUGUR operability: $($Operability.status)" -ForegroundColor $OperabilityColor

    if ($Operability.blockers -and $Operability.blockers.Count -gt 0) {
        Write-Host "Evidence blockers:"
        foreach ($Blocker in $Operability.blockers) {
            Write-Host "  - $Blocker"
        }
    }
}
catch {
    Write-Warning "Could not read AUGUR operability status: $($_.Exception.Message)"
}

$FrontendListeners = @(Get-PortListeners -Port $FrontendPort)
$ReuseFrontend = $false

if ($FrontendListeners.Count -gt 0) {
    $ForeignFrontendListeners = @($FrontendListeners | Where-Object { -not (Test-AugurProcess $_) })

    if ($ForeignFrontendListeners.Count -gt 0) {
        Show-PortConflict -Port $FrontendPort -Listeners $ForeignFrontendListeners
        throw "Cannot start AUGUR while port $FrontendPort is owned by another project or process."
    }

    try {
        $ExistingFrontend = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 2 -UseBasicParsing
        if ($ExistingFrontend.StatusCode -eq 200) {
            $ReuseFrontend = $true
            Write-Host "AUGUR frontend already running on $FrontendPort. Reusing it." -ForegroundColor Green
        }
    }
    catch {
        # Listener belongs to AUGUR but is not serving the frontend.
    }

    if (-not $ReuseFrontend) {
        throw "A stale AUGUR frontend is listening on port $FrontendPort but is not responding. Run .\stop-augur.ps1, then start AUGUR again."
    }
}

if (-not $ReuseFrontend) {
    Remove-Item $FrontendOut,$FrontendErr -Force -ErrorAction SilentlyContinue

    Write-Host "Starting AUGUR frontend on $FrontendPort..."
    $FrontendProcess = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList "run","dev" `
        -WorkingDirectory $Frontend `
        -RedirectStandardOutput $FrontendOut `
        -RedirectStandardError $FrontendErr `
        -PassThru

    $FrontendProcess.Id | Set-Content (Join-Path $RunDir "frontend.pid")

    $FrontendReady = $false

    for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
        Start-Sleep -Milliseconds 500

        $FrontendProcess.Refresh()

        if ($FrontendProcess.HasExited) {
            Write-Host ""
            Write-Host "AUGUR frontend failed to start." -ForegroundColor Red

            if (Test-Path $FrontendErr) {
                Get-Content $FrontendErr -Tail 80
            }

            throw "AUGUR frontend exited with code $($FrontendProcess.ExitCode)."
        }

        try {
            $Response = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 2 -UseBasicParsing
            if ($Response.StatusCode -eq 200) {
                $FrontendReady = $true
                break
            }
        }
        catch {
            # Vite may still be starting.
        }
    }

    if (-not $FrontendReady) {
        throw "AUGUR frontend did not become ready at $FrontendUrl."
    }
}

Write-Host ""
Write-Host "AUGUR running."
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend:  $BackendUrl"
Write-Host "API docs: $BackendUrl/docs"
Write-Host "Health:   $HealthUrl"
Write-Host "Data:     $OperabilityUrl"
Write-Host "Logs:     $LogDir"
Write-Host ""

Start-Process $FrontendUrl
