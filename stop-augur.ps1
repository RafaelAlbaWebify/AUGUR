$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir = Join-Path $Root ".run"

$ReservedPorts = @(8020, 5190)

function Stop-ProcessTree {
    param(
        [int]$ProcessId,
        [string]$Name
    )

    if (-not $ProcessId) {
        return
    }

    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $Process) {
        & taskkill.exe /PID $ProcessId /T /F | Out-Null
        Write-Host "Stopped AUGUR $Name process tree ($ProcessId)."
    }
}

foreach ($Name in @("frontend", "backend")) {
    $PidFile = Join-Path $RunDir "$Name.pid"

    if (Test-Path $PidFile) {
        $ProcessId = Get-Content $PidFile | Select-Object -First 1

        if ($ProcessId) {
            Stop-ProcessTree -ProcessId ([int]$ProcessId) -Name $Name
        }

        Remove-Item $PidFile -Force
    }
}

foreach ($Port in $ReservedPorts) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

    foreach ($Connection in $Connections) {
        $OwnerPid = $Connection.OwningProcess

        if (-not $OwnerPid) {
            continue
        }

        $CimProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $OwnerPid" -ErrorAction SilentlyContinue
        $CommandLine = $CimProcess.CommandLine
        $ExecutableName = $CimProcess.Name

        $LooksLikeAugur = (
            ($CommandLine -and $CommandLine -like "*$Root*") -or
            ($Port -eq 5190 -and $ExecutableName -eq "node.exe") -or
            ($Port -eq 8020 -and $ExecutableName -match "python")
        )

        if ($LooksLikeAugur) {
            & taskkill.exe /PID $OwnerPid /T /F | Out-Null
            Write-Host "Stopped stale AUGUR listener on port $Port (PID $OwnerPid)."
        }
        else {
            Write-Warning (
                "Port $Port is still in use by PID $OwnerPid ($ExecutableName), " +
                "but it does not look like AUGUR. It was not terminated."
            )
        }
    }
}
