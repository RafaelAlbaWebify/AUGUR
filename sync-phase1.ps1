$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment not found. Run setup-phase0.ps1 first."
}

Push-Location $Backend
try {
    & $Python -c "from app.db.bootstrap import initialize_datastores; from app.ingestion.world_bank import WorldBankAdapter; initialize_datastores(); a=WorldBankAdapter(); r=a.sync_country('ESP'); a.close(); print('AUGUR Phase 1 World Bank sync'); print('Country:', r['country_iso3']); print('Rows:', r['rows']); [print(' -', x['indicator_id'], x['rows'], 'rows') for x in r['indicators']]"
}
finally {
    Pop-Location
}
