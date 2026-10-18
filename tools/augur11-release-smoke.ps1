# AUGUR 11 release smoke: HTTP GET only, no DB initialization or sync.
param(
    [string]$BackendUrl = "http://127.0.0.1:8020",
    [string]$FrontendUrl = "http://127.0.0.1:5190",
    [string]$Output = (Join-Path $HOME "Downloads\AUGUR11_RELEASE_SMOKE.json")
)
$ErrorActionPreference = "Stop"
$results = [System.Collections.Generic.List[object]]::new()
function Probe([string]$Name, [string]$Url, [string[]]$RequiredKeys, [string]$ExpectedCountry) {
    $entry = [ordered]@{ name=$Name; url=$Url; status="FAIL"; http_status=$null; details=@(); duration_ms=0 }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 15 -UseBasicParsing
        $entry.http_status = [int]$response.StatusCode
        if ($entry.http_status -ne 200) { throw "HTTP $($entry.http_status)" }
        if ($RequiredKeys.Count -gt 0) {
            $data = $response.Content | ConvertFrom-Json
            foreach ($key in $RequiredKeys) {
                if (-not ($data.PSObject.Properties.Name -contains $key)) {
                    $entry.details += "Missing key: $key"
                }
            }
            if ($ExpectedCountry -and $data.country_iso3 -ne $ExpectedCountry) {
                $entry.details += "Unexpected country_iso3"
            }
        }
        if ($entry.details.Count -eq 0) { $entry.status="PASS" }
    } catch {
        $entry.details += $_.Exception.Message
    } finally {
        $watch.Stop()
        $entry.duration_ms = [math]::Round($watch.Elapsed.TotalMilliseconds)
        $results.Add([pscustomobject]$entry)
    }
}
Probe "frontend" $FrontendUrl @() ""
Probe "health" "$BackendUrl/api/health" @("status","datastores") ""
Probe "operability" "$BackendUrl/api/operability" @("status","ready","analysis_ready","blockers","country_analysis_ready") ""
Probe "countries" "$BackendUrl/api/countries" @("countries") ""
foreach ($code in @("ESP","PRT","IRL")) {
    Probe "snapshot_$code" "$BackendUrl/api/countries/$code/snapshot" @("country_iso3") $code
    Probe "trend_$code" "$BackendUrl/api/countries/$code/overview-series" @("country_iso3","series") $code
}
# This is a connectivity/contract smoke only; a 200 response cannot certify real source data.
$report = [ordered]@{
    schema_version=1
    generated_utc=(Get-Date).ToUniversalTime().ToString("o")
    scope="AUGUR11 release HTTP GET contract smoke (not product acceptance)"
    machine_data_excluded=$true
    requests=$results
    passed=@($results | Where-Object status -eq "PASS").Count
    failed=@($results | Where-Object status -ne "PASS").Count
    product_acceptance="NOT_CERTIFIED"
    limitations=@(
        "No independent observation/source comparison",
        "No authenticated profile or personalized-fit validation",
        "No UI interaction or screenshots",
        "No change to user DuckDB/SQLite",
        "No secret or full API response bodies included"
    )
}
$dir = Split-Path -Parent $Output
if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $Output
$results | Format-Table name,status,http_status,duration_ms -AutoSize
Write-Host "Report: $Output"
if ($report.failed -gt 0) { exit 2 }
exit 0
