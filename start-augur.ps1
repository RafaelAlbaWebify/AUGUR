$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$RunDir = Join-Path $Root ".run"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    throw "Frontend dependencies not found. Run setup-phase0.ps1 first."
}

Write-Host "Starting AUGUR backend..."
$BackendProcess = Start-Process `
    -FilePath $Python `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory $Backend `
    -PassThru
$BackendProcess.Id | Set-Content (Join-Path $RunDir "backend.pid")

Write-Host "Starting AUGUR frontend..."
$FrontendProcess = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList "run","dev" `
    -WorkingDirectory $Frontend `
    -PassThru
$FrontendProcess.Id | Set-Content (Join-Path $RunDir "frontend.pid")

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "AUGUR running."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host ""

Start-Process "http://127.0.0.1:5173"
