# Elevated Helper Down Runbook

## Trigger
`python elev.py <cmd>` exits 5 (helper on 127.0.0.1:8098 unreachable).

## Steps
1. Verify: `curl -s http://127.0.0.1:8098/health` returns nothing
2. Check if helper process running: `tasklist | findstr elev_helper`
3. Restart helper: `python memory/ops/elev_helper.py --daemon` (or scheduled task)
4. Verify: retry the original command via elev.py
5. Log incident to memory/ops/incidents/

## SLA
Detection immediate (exit code 5); recovery < 30s after restart
