# AUGUR 11 analytical evidence capture. GET-only; no installation, startup, sync, or DB writes.
param([string]$Output = (Join-Path $HOME "Downloads\AUGUR11_EVIDENCE.json"))
$ErrorActionPreference = "Stop"
$Base="http://127.0.0.1:8020"
function Fetch($route) { Invoke-RestMethod -Uri "$Base$route" -Method Get -TimeoutSec 25 }
$report=[ordered]@{schema_version=1; generated_utc=(Get-Date).ToUniversalTime().ToString("o"); scope="real local API evidence, NOT source-independent validation"; checks=@(); countries=@(); comparison=$null; warnings=@(); acceptance="NOT_CERTIFIED"}
try {
  $op=Fetch "/api/operability"
  $report.checks+=@{name="operability";status=$op.status;analysis_ready=$op.analysis_ready;country_analysis_ready=$op.country_analysis_ready;blockers=@($op.blockers)}
  foreach($iso in @("ESP","PRT","IRL")) {
    $snap=Fetch "/api/countries/$iso/snapshot"
    $hist=Fetch "/api/countries/$iso/overview-series"
    $items=@($snap.indicators)
    if($items.Count -eq 0) { $report.warnings+="snapshot_$iso : no 'indicators' array found or empty (schema needs review)" }
    $series=@($hist.series)
    $observed=@()
    foreach($s in $series) {
      $pts=@($s.points)
      $problems=@()
      if(-not $s.indicator_id -or -not $s.unit -or -not $s.source_id){$problems+="missing indicator/unit/source"}
      foreach($pt in $pts) {
        if($null -eq $pt.period -or $null -eq $pt.value) { $problems+="missing period/value" }
      }
      $last=$pts | Sort-Object period | Select-Object -Last 1
      $observed+=@{id=$s.indicator_id;source=$s.source_id;unit=$s.unit;count=$pts.Count;last_period=$last.period;last_value=$last.value;issues=@($problems)}
    }
    $report.countries+=@{country=$iso;series_count=$series.Count;series=@($observed)}
  }
  $cmp=Fetch "/api/compare?countries=ESP,PRT,IRL"
  $report.comparison=@{keys=@($cmp.PSObject.Properties.Name);status="response_received";country_codes=@("ESP","PRT","IRL")}
} catch {
  $report.warnings+="Capture error: $($_.Exception.Message)"
}
$report.overall_status=if($report.warnings.Count -eq 0){"CAPTURED_NOT_VALIDATED"}else{"REVIEW_REQUIRED"}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null
$report | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -Path $Output
Write-Host "AUGUR evidence: $Output"
Write-Host "Status: $($report.overall_status) / countries captured: $($report.countries.Count)"
