# smoke8_detached_r20.ps1 - ONE-SHOT, run ONCE on WHITE from the canonical root (dir containing agent_portal.py).
# Builder r20 (2026-11-14 auto-continue): closes TODO NEXT item "smoke8 when convenient".
# Launches smoke8.py DETACHED (serial-only through the portal; the portal's parallel_slots=1 queue means it
# simply waits behind the current chat turn - no parallel quinn-q4 traffic, so wedge #2 mechanism cannot trigger).
# Outputs: smoke8_r20.log + smoke8_result.json (incremental, verdict ALL_OK expected ~1-6 min).
$ErrorActionPreference = 'Stop'

if (-not (Test-Path .\agent_portal.py) -or -not (Test-Path .\smoke8.py)) {
  Write-Error "NOT the canonical root - cd to the folder with agent_portal.py + smoke8.py and re-run"; exit 1
}

# python resolver (console PATH first, then py launcher)
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "no python/py on PATH in this console"; exit 1 }
Write-Host "python = $py"

# 0) hash gate: smoke8.py pin measured r20 from shared-folder mirror (Black seat)
$expect = '520323ca051c044db6d5f0ff0ba6a497'
$actual = (Get-FileHash .\smoke8.py -Algorithm MD5).Hash.ToLower()
Write-Host "smoke8.py md5=$actual (expect $expect)"
if ($actual -ne $expect) { Write-Error "HASH MISMATCH - smoke8.py changed since pin; re-pin + re-review before running"; exit 1 }

# 1) single-instance gate (01:24 double-launch lesson): refuse while a smoke8 is already running
$running = Get-CimInstance Win32_Process -Filter "Name like '%python%'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*smoke8.py*' }
if ($running) {
  Write-Error ("smoke8 ALREADY RUNNING pid={0} - wait for it to finish, do NOT launch a second copy" -f (($running.ProcessId) -join ','))
  exit 1
}

# 2) portal liveness gate: without :8099 the smoke can only time out
$listener = (Get-NetTCPConnection -LocalPort 8099 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -First 1
if ($null -eq $listener) { Write-Error "no :8099 listener - portal down; run `schtasks /run /tn PortalRun` (or arnold-restart-r19.ps1) first, then this script"; exit 1 }
Write-Host ":8099 listener pid=$listener"

# 3) detached launch
$p = Start-Process -FilePath $py -ArgumentList 'smoke8.py' -WorkingDirectory (Get-Location).Path `
     -RedirectStandardOutput .\smoke8_r20.log -RedirectStandardError .\smoke8_r20_err.log -PassThru
Write-Host ("LAUNCHED smoke8 detached: pid={0}  log=smoke8_r20.log  result=smoke8_result.json" -f $p.Id)
Write-Host "Check back in ~3-6 min: Get-Content smoke8_result.json | Select-String verdict   (expect ALL_OK)"
Write-Host "Report verdict + per-agent secs to group -> Orchestrator closes the NEXT line item."
