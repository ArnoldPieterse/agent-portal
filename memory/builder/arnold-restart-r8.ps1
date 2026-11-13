# arnold-restart-r8.ps1 — ONE-SHOT, run ONCE on WHITE from the canonical root (dir containing agent_portal.py).
# Builder 2026-11-13. Zero file changes: White disk already carries b2a299ef (pull-exclusion); this only
# replaces the in-memory pre-fix process (PID 1240) with a fresh one. Runbook: memory/ops/windows-runbook.md.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path .\agent_portal.py)) { Write-Error "NOT the canonical root - cd to the folder with agent_portal.py and re-run"; exit 1 }

# 0) pre-state: assert current :8099 listener is the known stale PID
$old = (Get-NetTCPConnection -LocalPort 8099 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -First 1
Write-Host "pre: :8099 listener pid=$old (expected 1240)"
if ($old -ne 1240) { Write-Error "listener pid != 1240 - state drifted, ABORT and report to group"; exit 1 }

# 1) restart per runbook (taskkill FIRST - `schtasks /run` alone no-ops while Status=Running)
taskkill /pid $old /f | Out-Null
schtasks /run /tn PortalRun | Out-Null
Start-Sleep -Seconds 3
$new = (Get-NetTCPConnection -LocalPort 8099 -State Listen).OwningProcess | Select-Object -First 1
Write-Host "post: :8099 listener pid=$new"
if ($null -eq $new) { Write-Error "no listener after restart - check portal_run_err.log, re-run schtasks /run /tn PortalRun"; exit 1 }
if ($new -eq $old) { Write-Error "restart no-op: old PID still listening"; exit 1 }

# 2) runbook trap check: new process must postdate the code on disk
$code = (Get-Item agent_portal.py).LastWriteTime
$created = (Get-Process -Id $new).StartTime
Write-Host ("trap-check: created={0}  code_lastwrite={1}" -f $created, $code)
if ($created -le $code) { Write-Warning "CreationDate NOT > LastWriteTime - investigate before declaring done" } else { Write-Host "trap-check PASS" }
"$new" | Set-Content _portal_pid.txt

# 3) liveness proof (proxies Studio /api/inference/status; proves portal+Studio chain alive post-restart)
try {
  $s = (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8099/api/status).Content
  Write-Host "/api/status OK: " + $s.Substring(0, [Math]::Min(200, $s.Length))
} catch { Write-Error "/api/status probe failed: $_" }

Write-Host "DONE. New PID=$new (written to _portal_pid.txt). Hard-refresh portal tab (Ctrl+Shift+R). Report new PID + trap-check line to group -> Verifier closes AC-A2 process-level; Orchestrator resyncs MEMORY.md goal line now (post-restart only)."
