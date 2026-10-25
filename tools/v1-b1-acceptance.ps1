# B1 one-shot read-only live acceptance for ESP/IRL (no response bodies or PII).
param(
    [string]$BackendUrl = "http://127.0.0.1:8020",
    [string]$FrontendUrl = "http://127.0.0.1:5190",
    [string]$Output = (Join-Path $HOME "Downloads\AUGUR_V1_B1_ACCEPTANCE.json")
)
$ErrorActionPreference = "Stop"
$errors = [System.Collections.Generic.List[string]]::new()
$metrics = [ordered]@{}
$starting = (Get-Date).ToUniversalTime().ToString("o")
function Get-Json([string]$Path) {
    return Invoke-RestMethod -Uri "$BackendUrl/api$Path" -TimeoutSec 20
}
try {
    $page = Invoke-WebRequest -Uri "$FrontendUrl/compare?countries=ESP,IRL" -Method Get -TimeoutSec 20 -UseBasicParsing
    $metrics.frontend_http = [int]$page.StatusCode
} catch { $errors.Add("frontend_unreachable") }
try {
    $health = Get-Json "/health"
    $metrics.backend_health = $health.status
    $metrics.datastores_healthy = @($health.datastores.PSObject.Properties | Where-Object { $_.Value -ne $true }).Count -eq 0
    if ($health.status -ne "ok") { $errors.Add("backend_not_healthy") }
} catch { $errors.Add("backend_health_unavailable") }
try {
    $compare = Get-Json "/compare?countries=ESP,IRL"
    $metrics.compare_indicators = @($compare.indicators).Count
    if (@($compare.countries | ForEach-Object iso3) -join ',' -ne "ESP,IRL") {
        $errors.Add("unexpected_compare_country_order")
    }
    if (@($compare.indicators).Count -ne 29) { $errors.Add("compare_not_29") }
    if ($compare.indicator_count -ne @($compare.indicators).Count) { $errors.Add("compare_count_mismatch") }
    if ($compare.method -ne "aligned_current_observations_v1") { $errors.Add("compare_method_changed") }
    $metrics.mixed_year_indicators = @($compare.indicators | Where-Object {
        $_.countries.ESP -and $_.countries.IRL -and $_.countries.ESP.period -ne $_.countries.IRL.period
    }).Count
    $snapshotCounts = [ordered]@{}
    $trendCounts = [ordered]@{}
    $alignedCells = 0
    foreach ($country in @("ESP", "IRL")) {
        $snapshot = Get-Json "/countries/$country/snapshot"
        $trend = Get-Json "/countries/$country/overview-series"
        $snapshotCounts[$country] = @($snapshot.indicators).Count
        $trendCounts[$country] = @($trend.series).Count
        if ($snapshot.country_iso3 -ne $country -or $trend.country_iso3 -ne $country) {
            $errors.Add("identity_mismatch_$country")
        }
        if (@($snapshot.indicators).Count -ne 29) { $errors.Add("snapshot_not_29_$country") }
        $map = @{}
        foreach ($entry in $snapshot.indicators) { $map[$entry.indicator_id] = $entry }
        foreach ($row in $compare.indicators) {
            $found = $map[$row.indicator_id]
            $candidate = $row.countries.$country
            if ($null -eq $found -or $null -eq $candidate) {
                $errors.Add("missing_comparison_cell_$country"); continue
            }
            if ($found.period -ne $candidate.period -or
                $found.source_id -ne $candidate.source_id -or
                $found.unit -ne $row.unit -or
                [math]::Abs([double]$found.value - [double]$candidate.value) -gt 0.00000001) {
                $errors.Add("comparison_disagrees_with_snapshot_$country")
            } else {
                $alignedCells++
            }
        }
        foreach ($series in $trend.series) {
            $snap = $map[$series.indicator_id]
            $latest = @($series.points | Sort-Object period -Descending | Select-Object -First 1)
            if ($null -ne $snap -and $latest.Count -gt 0) {
                if ($snap.unit -ne $series.unit -or $snap.source_id -ne $series.source_id -or
                    $snap.period -ne $latest[0].period -or
                    [math]::Abs([double]$snap.value - [double]$latest[0].value) -gt 0.00000001) {
                    $errors.Add("trend_latest_mismatch_$country")
                }
            }
        }
    }
    $metrics.snapshot_counts = $snapshotCounts
    $metrics.trend_series_counts = $trendCounts
    $metrics.aligned_compare_cells = $alignedCells
    if ($alignedCells -ne 58) { $errors.Add("not_all_58_aligned") }
} catch { $errors.Add("compare_or_country_api_unavailable") }
$report = [ordered]@{
    schema_version=1
    generated_utc=$starting
    scope="B1 runtime and API consistency of local ESP/IRL compare. Does not certify browser rendering."
    status=if($errors.Count -eq 0){"API_PASS_BROWSER_PENDING"}else{"BLOCKED"}
    metrics=$metrics
    error_codes=@($errors.ToArray() | Select-Object -Unique)
    browser_acceptance="NOT_YET_OBSERVED"
    preservation="NO_DB_WRITE_FROM_THIS_SCRIPT; STARTUP_SIDE_EFFECTS_NOT_AUDITED"
    source_provenance="Reuse separate, already accepted 58/58 source-vintage report; not reaudited"
    limitations=@("No JavaScript/browser DOM interaction", "No user profile reads", "No database mutation or ingestion", "No API payload values or personal data saved")
}
$dir=Split-Path -Parent $Output
if($dir){New-Item -ItemType Directory -Force -Path $dir | Out-Null}
$report | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 $Output
$report | ConvertTo-Json -Depth 4
Write-Host "B1 evidence: $Output"
if($errors.Count -gt 0){exit 2}
