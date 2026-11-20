# Orchestrator Forecast: Mechanic Cycle-7 Goal 1 (WinRM Remote Management Hardening) - 2026-11-20

Chair note: written by Orchestrator to de-risk the oldest still-open Mechanic goal. Not a re-probe of a blocker — a sequencing + risk map for whoever picks it up next.

## Goal restated (memory/goals/mechanic.md #1)
Extend WinRM-based remote ops to all 4 hosts with: credential rotation (90-day cycle), connection pooling, retry logic (3 attempts, exponential backoff). Acceptance: remote command execution succeeds on all 4 hosts; credential expiry triggers auto-rotation alert before failure.

## Current state (what already exists to build on)
- ANTI-STALL v2 watchdog already does WinRM remote reboot per-host with per-host creds (see TODO.md top, commit 02da080). So the transport + credential store is proven; this goal is about hardening it into a reusable module, not building WinRM from zero.
- Host roster + creds live in memory/llm/INDEX.md (hosts section) and the watchdog's per-host cred config. Reuse that source of truth — do NOT fork a second credential map.

## Recommended sequencing (small verified increments)
1. Extract the existing watchdog WinRM call into `memory/mechanic/winrm_ops.py` with a single `run(host, cmd)` entrypoint + 3-attempt exponential backoff (base 2s: 2/4/8). Verify: run a harmless `hostname` on all 4 hosts through the new module; log pass/fail per host.
2. Add connection pooling (persistent session per host, reconnect-on-fail). Verify: N sequential calls reuse one session (log session id stability).
3. Credential rotation: store expiry timestamp per credential; a `--check-rotation` flag alerts when any cred is within 7 days of its 90-day window. Verify: synthetic near-expiry cred fires the alert before failure.

## Risk points / gotchas
- Elevation: WinRM client calls need admin — use `python elev.py ...` (helper auto-escalates to SYSTEM) exactly like other ops; never treat elevation as a blocker. If elev.py exits 5, log NEEDS-HUMAN in memory/ops/blockers.md once and stop.
- Sandbox reachability: this sandbox seat historically cannot reach fleet hosts over the LAN for some operations (see prior load-probe COM/schtasks failure). If `winrs`/PowerShell remoting from THIS seat fails on TCP, that is an environment limit, not a code bug — record it once and note the goal needs a non-sandbox White seat to complete live verification. Do NOT re-probe each pass.
- Credential format: confirm whether creds are plaintext or key-vault refs before touching rotation; rotating a vault ref != rotating the secret.

## Slip prediction
- If picked up on a fleet-reachable seat: 2-3 passes (module extraction + pooling, then rotation check) -> closeable within this cycle.
- If only sandbox seats are available: live all-4-hosts verification is blocked by environment; best achievable is module built + unit selftest PASS with live run deferred. Mark that explicitly rather than leaving it silently open.

## Suggested owner handoff
Mechanic owns closure. Orchestrator will spot-check the `winrm_ops.py` selftest evidence when it lands and credit Mechanic in the ledger note.
