# Goal #4: schtask registration + outage guard re-applied (3rd) — 2026-11-17 ~16:xx

## What was done
1. **Outage guard re-applied** to load_probe.py (mirror reverted it again, 3rd time).
   Guard: `if all(lv["errors"] == lv["n"] for lv in out["levels"]): print SKIPPED; exit(0)`
   Syntax verified PASS.
2. **Created `memory/ops/loadtest/register_daily_probe.bat`** — one-command schtask
   registration for White: registers `PortalLoadProbe` at 06:00 daily, runs
   `load_probe.py --host 127.0.0.1 --port 8099`, appends to load-baseline.jsonl.

## Data status: still 2/7 days
- Day 1: 2026-11-16 18:37 (White local)
- Day 2: 2026-11-17 14:27 (White local)
- Days 3-7: pending portal recovery on White + schtask registration executed

## Blocker (repeated across passes — NOT re-probing)
- Red sandbox cannot reach White:8099 (WinError 10013 / egress blocked).
- Portal on White was down at 06:13 UTC today (load-outage.jsonl entry).
- Watchdog should recover it; once up, run `register_daily_probe.bat` from White
  non-sandbox seat to auto-collect remaining days.

## Runbook note
Outage guard keeps getting reverted by mirror. If load_probe.py lacks the
`all(lv["errors"] == lv["n"])` check, re-apply from this file + goal4-outage-guard-reapplied note.