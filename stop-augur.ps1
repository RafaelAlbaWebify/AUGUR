$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir = Join-Path $Root ".run"

$ReservedPorts = @(8020, 5190)

function Get-ProcessInfo {
    param([int]$ProcessId)

    return Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Test-AugurProcess {
    param([int]$ProcessId)

    $process = Get-ProcessInfo -ProcessId $ProcessId
    return (
        $null -ne $process -and
        $process.CommandLine -and
        $process.CommandLine -like "*$Root*"
    )
}

function Stop-AugurProcessTree {
    param(
        [int]$ProcessId,
        [string]$Name
    )

    if (-not $ProcessId) {
        return
    }

    if (-not (Test-AugurProcess -ProcessId $ProcessId)) {
        $process = Get-ProcessInfo -ProcessId $ProcessId
        $processName = if ($process) { $process.Name } else { "unknown" }
        Write-Warning "PID $ProcessId ($processName) does not belong to this AUGUR checkout. It was not terminated."
        return
    }

    & taskkill.exe /PID $ProcessId /T /F | Out-Null
    Write-Host "Stopped AUGUR $Name process tree ($ProcessId)."
}

foreach ($Name in @("frontend", "backend")) {
    $PidFile = Join-Path $RunDir "$Name.pid"

    if (Test-Path $PidFile) {
        $ProcessId = Get-Content $PidFile | Select-Object -First 1

        if ($ProcessId) {
            Stop-AugurProcessTree -ProcessId ([int]$ProcessId) -Name $Name
        }

        Remove-Item $PidFile -Force
    }
}

foreach ($Port in $ReservedPorts) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

    foreach ($Connection in $Connections) {
        $OwnerPid = [int]$Connection.OwningProcess

        if (-not $OwnerPid) {
            continue
        }

        $process = Get-ProcessInfo -ProcessId $OwnerPid
        $processName = if ($process) { $process.Name } else { "unknown" }

        if (Test-AugurProcess -ProcessId $OwnerPid) {
            & taskkill.exe /PID $OwnerPid /T /F | Out-Null
            Write-Host "Stopped stale AUGUR listener on port $Port (PID $OwnerPid)."
        }
        else {
            Write-Warning (
                "Port $Port is still in use by PID $OwnerPid ($processName), " +
                "but it does not belong to this AUGUR checkout. It was not terminated."
            )
        }
    }
}
