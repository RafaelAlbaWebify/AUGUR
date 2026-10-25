# AUGUR global module availability evidence: read-only GET, sanitized JSON report.
param(
  [string]$BackendUrl = "http://127.0.0.1:8020",
  [string]$FrontendUrl = "http://127.0.0.1:5190",
  [string]$Output = (Join-Path $HOME "Downloads\AUGUR_GLOBAL_OPERABILITY.json")
)
$ErrorActionPreference = "Stop"
$checks = [System.Collections.Generic.List[object]]::new()
function Check([string]$Module, [string]$Name, [string]$Path, [string[]]$Keys) {
  $url = if ($Module -eq "frontend") { "$FrontendUrl$Path" } else { "$BackendUrl/api$Path" }
  $timer = [Diagnostics.Stopwatch]::StartNew()
  $entry = [ordered]@{ module=$Module; name=$Name; status="unavailable"; http_status=$null; elapsed_ms=$null; issues=@() }
  try {
    $r = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 12 -UseBasicParsing
    $entry.http_status = [int]$r.StatusCode
    if ($entry.http_status -ne 200) { throw "Unexpected HTTP $($entry.http_status)" }
    if ($Keys.Count -gt 0) {
      $data = $r.Content | ConvertFrom-Json
      foreach ($key in $Keys) {
        if ($data.PSObject.Properties.Name -notcontains $key) {
          $entry.issues += "missing_field:$key"
        }
      }
    }
    if ($entry.issues.Count -eq 0) { $entry.status="reachable_contract" } else { $entry.status="contract_failure" }
  } catch {
    $entry.issues += $_.Exception.GetType().Name
  } finally {
    $timer.Stop()
    $entry.elapsed_ms = [math]::Round($timer.Elapsed.TotalMilliseconds)
    $checks.Add([pscustomobject]$entry)
  }
}
Check frontend homepage "/" @()
Check infrastructure health "/health" @("status","datastores")
Check infrastructure operability "/operability" @("status","ready","blockers")
Check national countries "/countries" @("countries")
Check national compare "/compare?countries=ESP,IRL" @("countries","indicator_count","indicators")
Check national esp_snapshot "/countries/ESP/snapshot" @("country_iso3")
Check national irl_snapshot "/countries/IRL/snapshot" @("country_iso3")
Check national trend "/countries/ESP/overview-series" @("country_iso3","series")
Check national evidence_status "/evidence/status" @()
Check geography geographic_coverage "/geographies/coverage" @()
Check geography subnational_status "/subnational/status" @()
Check rankings region_rankings "/rankings/regions?indicator_id=regional_employment_rate&countries=ESP,IRL" @("status","indicator_id","observed_rows","eligible_total","items")
Check profile readiness "/profile/readiness" @()
Check profile personal_profile "/profile" @()
Check personal_fit personalized_compare "/compare/personalized?countries=ESP,IRL" @()
Check personal_fit financial_fit "/countries/ESP/financial-fit" @()
Check personal_fit legal_fit "/countries/ESP/legal-fit" @()
Check career esco_status "/esco/status" @()
Check career career_fit "/countries/ESP/career-fit" @()
Check ttv calibration_status "/ttv/calibration/status" @()
Check ttv country_ttv "/countries/ESP/ttv" @()
$results = @($checks.ToArray())
$moduleScores = @($results | Group-Object module | ForEach-Object {
  [pscustomobject]@{module=$_.Name; reachable=@($_.Group | Where-Object status -eq "reachable_contract").Count; total=$_.Count}
})
$report = [ordered]@{
  schema_version=1
  generated_utc=(Get-Date).ToUniversalTime().ToString("o")
  scope="GET-only module reachability and shallow response contracts; NOT functional acceptance"
  checks=$results
  modules=$moduleScores
  known_existing_evidence=[ordered]@{
    esp_irl_national_comparison="accepted: 58/58 data observations; prior operator report"
    regional_nuts2_rankings="blocked pending boundary vintage and quality flags per GR2 project report"
    ttv_full_release="blocked pending prospective external holdout under frozen protocol"
    personal_fit="not accepted with an actual operator profile"
  }
  source_data_included=$false
  operational_release_certified=$false
  limitations=@(
    "Endpoint HTTP 200 does not certify algorithm, population coverage, ranking comparability, or personal fit correctness",
    "No browser interactions or fresh source audits",
    "No user profile values, API response bodies or secrets saved",
    "GET only; never initializes, migrates or writes databases from this script"
  )
}
$parent=Split-Path -Parent $Output
if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
$report | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 $Output
$results | Format-Table module,name,status,http_status -AutoSize
Write-Host "Saved read-only global module report: $Output"
