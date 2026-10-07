param(
    [string]$Input = "",
    [int]$MaxRows = 80
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "AUGUR virtual environment not found. Run .\bootstrap-augur.ps1 first."
}

$Arguments = @(
    "-m", "scripts.inspect_cedefop_clssi",
    "--max-rows", "$MaxRows"
)

if ($Input) {
    $Arguments += @(
        "--input",
        (Resolve-Path $Input).Path
    )
}

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
    Write-Host "CLSSI workbook schema candidate detected." -ForegroundColor Green
    exit 0
}

if ($Code -eq 2) {
    Write-Warning "CLSSI workbook downloaded/read successfully, but its schema is not yet mapped safely. Review the JSON diagnostic; no analytical data were written."
    exit 2
}

throw "CLSSI inspection failed with exit code $Code."
