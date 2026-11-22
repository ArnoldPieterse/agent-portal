# Goal 4: load_probe.py remote-host upgrade + reachability finding (2026-11-17)

## What was done
Upgraded `memory/ops/load_probe.py`:
- Added `--host` and `--port` CLI args (default 127.0.0.1:8099 for local runs)
- Added preflight socket check that logs a structured UNREACHABLE entry to load-baseline.jsonl
  instead of silently writing all-error data points
- Extended error message truncation from 40→80 chars for better diagnostics
- Syntax verified (py_compile PASS)

## Key finding: portal unreachable from Red
- White (White):8099 times out from Red (Red) — both TCP connect and HTTP
- Portal cannot be started locally on Red: sandbox restricts C:\Users enumeration, breaking
  `_find_sandbox_dir()` in agent_portal.py
- **Operational requirement**: the daily load probe scheduled task MUST run ON White
  (where the portal lives), not from a remote host. This is consistent with how the first
  baseline was captured (2026-11-16, local to White).

## Baseline data status
- Day 1: 2026-11-16 18:37 (p50=127ms@10, 373ms@50, 1666ms@200; 0 errors) ✓
- Day 2+: blocked until probe runs from White. Script is ready (`--host` arg makes it
  explicit which host was probed in the JSONL entry).

## Next step (when White is reachable / portal running)
Run on White: `python memory/ops/load_probe.py --host 127.0.0.1 --port 8099`
Or from any host with network access: `python memory/ops/load_probe.py --host White --port 8099`

One-line runbook: load_probe.py now supports remote targeting; daily probe must execute on the portal host (White) because Red sandbox blocks both outbound to White:8099 and local portal startup.
