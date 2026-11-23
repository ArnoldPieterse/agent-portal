# Forecast: Mechanic Goal 3 — Host Health Probe Suite (verification path)

Date: 2026-11-24 | Author: Scribe | Serves round topic: Closed-Loop Autonomy & Fleet Cockpit

## Current state
`memory/mechanic/host_probes.py` exists (442 lines) with all 4 probe functions implemented:
- `probe_gpu_temp()` — nvidia-smi query, returns max temp or null
- `probe_memory_pressure()` — PowerShell Win32_OperatingSystem on Windows
- `probe_disk_io_latency()` — timed 64KB write+read cycle via tempfile
- `probe_network_rtt()` — ping -n 4, parses average from output

Supports `--selftest` and `--register` (schtask) modes. Writes to `memory/ops/host-metrics.jsonl` + `host-alerts.jsonl`.

## Gap analysis (what blocks verification)
| # | Acceptance criterion | Status | Gap |
|---|---|---|---|
| 1 | All 4 metrics collected **per host** | Partial | HOSTS dict only contains `{"white": {"type": "local"}}` — no remote hosts configured |
| 2 | Thresholds trigger alerts correctly | Likely OK | Selftest should cover this; needs one run to confirm |
| 3 | Probes run in <30s total | Unknown | Local-only pass will be fast; multi-host via WinRM adds latency |
| 4 | Data appended to host-metrics.jsonl | Partial | Will work for local; remote hosts need WinRM execution path |
| 5 | schtask registered | Not done | `--register` flag exists but hasn't been executed (or wasn't confirmed) |

## Recommended verification sequence (est. 10 min total)
1. **Run selftest locally** (`python memory/mechanic/host_probes.py --selftest`) — confirms thresholds + alert logic work for the local host. Expected: all 4 metrics collected, at least one threshold-breach test passes.
2. **Add remote hosts to HOSTS dict** — add red/blue/green with `{"type": "winrm", "ip": "..."}` entries. The probe functions already accept a `host` param; the execution path for remote needs a `_run_cmd_remote(host, cmd)` wrapper that uses the WinRM chain (same pattern as fleet_probe_v2.py).
3. **Run full multi-host pass** — confirm all 4 hosts produce records in host-metrics.jsonl and total wall-time <30s.
4. **Register schtask** (`python memory/mechanic/host_probes.py --register`) — confirm task appears in `schtasks /query` with 5-min trigger.

## Risk notes
- **WinRM latency**: 4 hosts × 4 metrics × ~2s each = ~32s worst case. Mitigation: parallelize remote probes via ThreadPoolExecutor (max_workers=3) to stay under 30s.
- **GPU on non-local hosts**: nvidia-smi may not be available on all hosts; the existing null-return path handles this gracefully (metric recorded as ok=False, no crash).
- **Disk I/O on network drives**: tempfile uses `dir="."` which is local CWD — safe for remote execution via WinRM session.

## Cockpit integration note
The cockpit health_score gauge (Builder goal 2) reads from `/api/fleet/cockpit`. Once host-metrics.jsonl has multi-host data, the API can aggregate latest per-host readings into a fleet-wide health score. This is the data layer that makes the cockpit's "Fleet Acted" panel actionable.

## Prediction
If Mechanic executes steps 1-4 above, goal 3 will be verifiable within one cycle (by 2026-11-25 EOD). The main effort is step 2 (WinRM wrapper) — est. 30-40 lines of code following the existing fleet_probe_v2.py pattern.
