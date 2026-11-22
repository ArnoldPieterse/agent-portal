# Live-Run Checklist (Non-Sandbox White Seat)
**Purpose:** Single-pass script to close all "live run from non-sandbox seat" items blocking multiple agents.
**Prereq:** Must run from a seat where `http://127.0.0.1:8099` is reachable (White, not sandbox).
**Date:** 2026-11-21

## Items to execute (in order):

### 1. Verifier #4 - Performance Gate Baseline
```bash
python memory/verifier/perf_gate.py --baseline
```
**Accepts:** perf-baseline.json written with p50/p95 for all endpoints; exit 0.
**Evidence:** `memory/verifier/perf-baseline.json` + one-line in goal_ledger.

### 2. Mechanic #1 - Portal Load Test (7-day completion)
```bash
python memory/mechanic/goal1_auto_closure.py --week-complete
```
**Accepts:** load_trend.jsonl has >=7 unique days; closure verdict (PASS/FAIL) written.
**Evidence:** `memory/mechanic/load-test-week.md` updated with final day count + verdict.

### 3. Mechanic #3 - WinRM E2E (live leg)
```bash
python memory/mechanic/winrm_e2e_test.py --live --target Black
```
**Accepts:** full anti-stall cycle completes <15 min; log entries in correct order.
**Evidence:** `memory/mechanic/winrm-e2e-live-<date>.md` with timestamps.

### 4. Mechanic #4 - Fleet Status CB (live leg)
```bash
python memory/mechanic/goal4-live-integration-test.py --live
```
**Accepts:** circuit breaker opens after 3 real failures; partial data returned for other hosts.
**Evidence:** `memory/mechanic/goal4-live-<date>.md` with request/response samples.

### 5. Mechanic #9 - Capacity Planning (live leg)
```bash
python memory/mechanic/capacity_report.py --live
```
**Accepts:** 7-day VRAM data from load_trend.jsonl; trend line + prediction written.
**Evidence:** `memory/mechanic/capacity-plan-<date>.md` with prediction accuracy note.

## Post-execution:
- Run `python memory/researcher/goal_ledger.py --record <agent> <goal#> --note '<artifact>'` for each closed item.
- Update MEMORY.md goal line if fleet % changes.
