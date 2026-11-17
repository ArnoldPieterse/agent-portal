# Mirror-Revert Correlation Tool + Pre-Window Burst Finding (goal #3)
Date: 2026-11-18 (auto-loop, day ~2/7) — forward step on goal #3 WITHOUT re-probing the seed wall.

## What was built
`memory/researcher/mirror_revert_correlate.py` — the ROOT-CAUSE bridge that was missing from
goal #3's closure path. It overlays LIVE mirror revert events onto the on-disk pin-file timeline
(`_pin_timeline_raw.json`) and attributes each revert to an **automated burst window** (consecutive
same-kind re-pins with gap < 300s, chains merged) vs organic drift. This tests hypothesis #2
("automated feedback cycle", from the analysis template) against live data.

Key property: it is **independent of the blocked seed wall**. It consumes whatever live log exists
and degrades gracefully when empty (reports pre-window baseline only). Stdlib-only. Day-7 closure
for the root-cause section is now a second one-command step after `parse_mirror_events.py`.

## Validation (no crash, correct shape)
- TEST A — no live log: graceful degrade; prints 0 live reverts + pre-window baseline per kind.
- TEST B — synthetic 7-day dataset (11 reverts): per-path overlay renders; index.html=7,
  ui/core.js=2, memory/INDEX.md=2(no-pin). Verdict logic exercised (thresholds >=60%/25-60%/<25%).

## NEW pre-window measurement (from disk alone — the concrete step this pass)
index.html = 46 pins over the pre-window. Of 45 consecutive re-pin transitions, **12 are <300s
(26.7%)** vs a median gap of 671s (~11 min). That is a **bimodal cadence**: ~1/4 of index.html
re-pins fire in rapid automated bursts (min gap = **16.2s**) while the rest are human-scale edits.
A 16-second re-pin cycle is physically too fast for copy+sha+commit — quantitative confirmation,
from disk alone, that hypothesis #2 (automated clobber loop) is a real mechanism, not just an edit-heavy day.

## Status / next
- Goal #3 STILL OPEN: acceptance still requires the one-week LIVE dataset (window 11-17->11-24).
- At ~11-24 closure = `python memory/researcher/parse_mirror_events.py <live-log>` THEN
  `python memory/researcher/mirror_revert_correlate.py <live-log>` -> frequency table + root-cause read.
- Seed wall NOT re-probed (anti-loop). Next checkpoint = 11-20 day-3 escalation per runbook ladder.
