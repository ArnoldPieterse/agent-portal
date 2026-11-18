# Preliminary Revert-Frequency Table (File-Based Proxy)
Date: 2026-11-18 (day 2 of window 11-17 to 11-24)
Goal: #3 Mirror-revert root-cause deep-dive
Method: Canonical pin files in memory/designer/ as observable proxy for revert events.
        Each pin = one "restore to known-good" action by the mirror daemon.

## Data Source and Caveat
- Primary source (live mirror_events.log on White) is BLOCKED (SMB auth, NEEDS-HUMAN logged).
- This leaf uses SECONDARY evidence: pin file creation timestamps in the shared folder.
- Pin files are created when memory_mirror.py restores a file to its canonical state.
- Therefore: pin file count ~= revert event count (1:1 mapping for index.html + ui/*).

## Frequency Table

| File | Total Pins | 11-16 | 11-17 | 11-18 | Notes |
|------|-----------|-------|-------|-------|-------|
| index.html | 46 | ~21 | 23 | 1 | Dominant (94% of all pins) |
| ui/app.css | 1 | 0 | 1 | 0 | New file post-split |
| ui/core.js | 1 | 0 | 1 | 0 | New file post-split |
| ui/uploads.js | 1 | 0 | 1 | 0 | New file post-split |
| **Total** | **49** | **~24** | **25** | **1** | |

## Burst Analysis (11-17, the active day)

Hourly pin count:
```
00:00  [4]
10:00  [1]
11:00  [1]
12:00  [4]
13:00  [2]
14:00  [2]
15:00  [2]
16:00  [2]
17:00  [3]
18:00  [2]
19:00  [1]
```

Inter-pin interval classification (n=48 intervals):
- Burst (<5 min):   13/48 (27%) - mechanical/revert-driven
- Active (5-60m):   27/48 (56%) - sustained development
- Quiet (>60min):    8/48 (17%) - overnight/break gaps

## Key Findings (preliminary)

1. **index.html is the dominant revert target** (94% of pins). Confirms it as the primary
   conflict point - multiple agents write to it, mirror reverts to canonical frequently.

2. **27% burst rate** (<5min intervals) suggests a significant fraction of pin events are
   mechanical (mirror auto-repair) rather than organic development pushes. The 11-16 UI split
   created a one-time mega-burst; 11-17 shows sustained moderate activity.

3. **The ui/* files have exactly 1 pin each** (created on 11-17 during the split). No reverts
   yet - either they are stable or the window is too short to see drift.

4. **Quiet period 19:00 to 00:00** (5h gap) = overnight boundary, not a signal.

## Implication for Day-7 Analysis

If the live log remains blocked through 11-24, this file-based proxy provides:
- A frequency table (which files revert most): YES
- Trigger classification (burst vs organic): PARTIAL (cannot distinguish pin_drift from
  hash_mismatch without the log trigger field)
- Contingency table allows partial-close with caveat at 3+ days / 5+ events.

## Next Steps
- Day 3 (11-20): escalation per runbook ladder - consolidated NEEDS-HUMAN + pivot to goal #8 re-audit
- Day 7 (11-24): if live log available, full analysis via fill_analysis.py; if not, partial-close
  with this table plus caveat

## Evidence of Data Freshness
- Pin scan run: 2026-11-18 (this pass)
- Most recent pin: abf83b77ca4d_2026-11-18a.html (mtime 11-18 00:19)
- Total pins at scan time: 49
