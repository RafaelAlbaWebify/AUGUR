$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir = Join-Path $Root ".run"

foreach ($Name in @("frontend", "backend")) {
    $PidFile = Join-Path $RunDir "$Name.pid"
    if (Test-Path $PidFile) {
        $ProcessId = Get-Content $PidFile | Select-Object -First 1
        if ($ProcessId) {
            Stop-Process -Id ([int]$ProcessId) -Force
            Write-Host "Stopped AUGUR $Name process ($ProcessId)."
        }
        Remove-Item $PidFile -Force
    }
}
