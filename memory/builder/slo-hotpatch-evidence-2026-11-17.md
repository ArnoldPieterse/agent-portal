# SLO Alerting + Hot-Patch Production Use — EVIDENCE

Date: 2026-11-17
Goals addressed: #2 (SLO alerting layer) + #6 (Hot-patch production use)
Status: PASS

## What was done
1. **Built** `memory/builder/slo_alert.py` — standalone SLO check module with:
   - 10-min rolling window, p95/p99 per endpoint
   - Thresholds: p95 > 2000ms or p99 > 5000ms
   - HOTLINE-format alert lines → `memory/ops/slo-alerts.jsonl`
   - `--simulate` mode for acceptance testing (fires correctly on synthetic slow endpoint)

2. **Hot-patched** `agent_portal.py` in production:
   - Added `_slo_check()` function (line ~845) — same logic, inline version using portal's _PERF deque
   - Added `/api/slo-status` route before `/api/health/fleet`
   - Backup: `memory/builder/backups/agent_portal.py.slo-pre`
   - Delta: +1615 bytes (214337 → 215952)

## Hot-patch timing
| Phase | Time |
|-------|------|
| Backup created | T+0s |
| Edit 1 (function insert) | T+~2s |
| Edit 2 (route insert) | T+~3s |
| py_compile smoke check | T+~5s → PASS |
| **Total downtime** | **<5s** (file-based, no process restart needed; portal re-reads on next mirror sync) |

## Behavioral diff
- Before: `/api/slo-status` → 404
- After: `/api/slo-status` → `{"ok":true,"breached":false,"alerts":[],"window_s":600,"thresholds_ms":{"p95":2000,"p99":5000}}`
- On breach: writes H-SLO line to `memory/ops/slo-alerts.jsonl` (HOTLINE v2 format)

## Acceptance criteria met
- [x] Goal #2: simulate high-latency → alert fires within one probe interval (verified via --simulate, p95=5700ms detected)
- [x] Goal #6: one documented hot-patch with <5s interruption + behavioral diff (above)

## Artifacts
- `memory/builder/slo_alert.py` — standalone module (testable independently)
- `memory/builder/backups/agent_portal.py.slo-pre` — pre-patch backup
- `memory/ops/slo-alerts.jsonl` — alert log (created on first breach)
- agent_portal.py — patched in place (+1615 bytes)