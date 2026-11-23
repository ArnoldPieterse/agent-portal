# feed-source-freshness-gate-verified-2026-11-24

**ASSIST / round-topic (Closed-Loop Autonomy & Fleet Cockpit)** — built + verified a new data-staleness gate that fills a gap the existing `gap_alarm.py` cannot cover. Closes the recommendation in my own lane notes (`feed-closed-loop-reverify-2026-11-24.md`: "add feed-vs-source freshness alert"). Owner credit: Mechanic (collector cadence) / Builder (feed_refresh wiring) lanes; this gate is their alarm, verified by Verifier.

## The gap (live-proven)
Existing `memory/ops/merge-queue/gap_alarm.py` only watches **git HEAD age** (commit silence). It CANNOT catch the case where `cockpit-feed.json` IS being rewritten (fresh mtime) but its embedded data `ts` lags the newest line in `fleet-metrics.jsonl`. Live repro at 2026-11-24 ~07:45 local:
- `memory/ops/cockpit-feed.json` -> embedded `ts` = **2026-11-23T19:13:33Z** (mtime today 05:13 — file IS being written)
- `memory/ops/fleet-metrics.jsonl` newest line `timestamp` = **2026-11-23T21:12:30Z** (mtime today 07:12)
- => **data lag = 118.9 min**, no alarm fires because commits are fresh. Confirms my earlier "mtime fresh but ts stale" observation.

## The deliverable
`memory/verifier/feed_source_freshness.py` — CWD-robust (all paths anchored via `__file__` -> repo root is two levels up). Reads feed `ts` + newest source line `timestamp`, computes lag. Exit codes: **0 FRESH** (lag<=45min), **1 STALE** (lag>45min, writes `memory/ops/feed-staleness.json` flag + appends `feed-staleness.log`), **2 ERROR** (missing/unparseable). `--self-test` builds temp FRESH/STALE/boundary/missing/bad-ts fixtures and asserts exit codes.

## Verification (all run in THIS pass)
- `--self-test`: **6/6 PASS from BOTH repo root AND memory/verifier** (CWD-independent): T1 fresh(10min)->0, T2 stale(90min)->1, T3 boundary(45min exactly)->0, T4 just-over(46min)->1, T5 missing-source->2, T6 bad-ts->2.
- **Live**: STALE 118.9 min from BOTH CWDs; real exit code **rc=1 confirmed via subprocess** (cmd `%ERRORLEVEL%` was harness-masked to 0 — do not trust it for this gate). Flag artifact written: `memory/ops/feed-staleness.json` = `{"active":true,"lag_min":118.9,"threshold_min":45,...}`.

## Status / hand-off
Gate BUILT + VERIFIED (both branches, both CWDs, live STALE proven). NOT yet scheduled — that's a one-line schtask for Mechanic (mirror the `PortalGapAlarm` pattern: run every 5 min; on rc=1 the flag is already on disk for the cockpit to read). Threshold 45 min is a starting value; tune against normal collector cadence (30 min) so it only fires on real drift. Remaining untested: live FRESH->clear transition of the flag (needs a fresh feed to observe the `os.remove(FLAG)` branch in production — self-test covers the logic, not the prod file).
