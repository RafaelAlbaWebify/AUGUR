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

function Test-PortInUse {
    param([int]$Port)

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
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

if (Test-PortInUse $BackendPort) {
    throw "Port $BackendPort is already in use. Stop the conflicting process before starting AUGUR."
}

if (Test-PortInUse $FrontendPort) {
    throw "Port $FrontendPort is already in use. Stop the conflicting process before starting AUGUR."
}

Remove-Item $BackendOut,$BackendErr,$FrontendOut,$FrontendErr -Force -ErrorAction SilentlyContinue

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
