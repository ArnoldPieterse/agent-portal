# Mirror-Revert — REAL Failed-Restore Data from the Discarded Log Stream (goal #3)

Date: 2026-11-18 (auto-loop pass). Window day 2/7 (11-17→11-24).
Owner: Researcher. Independent of the blocked live-mirror seed — mines data ALREADY on disk.

## What this is
The day-7 frequency table parses ONLY `Z:\mirror_events.log` (`log_event`). But pin_guard's
FAILED restores never call `log_event` — they append only to `memory_mirror.log` under the
`pin_guard` key (memory_mirror.py:286-287 vs the successful path 281-285 which DOES log_event).
So the frequency table SYSTEMATICALLY UNDERCOUNTS reverts. This leaf captures that real data now.

## Source read (raw, verbatim) — memory\mirror.log (848 B)
```
{"t": "2026-11-17 23:35:50", "pin_guard": [{"file": "index.html", "was": "fdc359022109", "error": "backup missing/wrong sha"}]}
{"t": "2026-11-17 23:36:58", "results": [Red/Pale/Black all "System error 5 Access is denied"], "pin_guard": [{"file": "index.html", "was": "fdc359022109", "error": "backup missing/wrong sha"}]}
```

## Findings (real, in-window data — NOT synthetic)
1. **Two real failed pin restores on 11-17 23:35 & 23:36** — ~40 min AFTER the 20:53 self-test _test lines.
   These are genuine in-window events (window opened 11-17), invisible to mirror_events.log.
2. **File = index.html, both times** — corroborates the pin-churn finding (index.html ≈94% of churn).
3. **`was=fdc359022109`**: index.html had drifted OFF its pinned sha (spec expected a different sha12),
   i.e. a clobber/flap event occurred and pin_guard tried to restore it.
4. **NEW trigger class = `backup missing/wrong sha`** (error path, line 287): the canonical backup
   itself was absent or had a wrong sha, so auto-repair SILENTLY GAVE UP — no copy, no utime, no event log.
   This is MORE SEVERE than successful pin_drift: it means pin protection has a hole (drift + bad backup = un-repaired).
5. **Confirms schema de-check undercount prediction** with live data: the frequency table will miss every
   such failed-restore unless we ALSO parse memory_mirror.log pin_guard entries.

## Implication for day-7 closure (concrete requirement added)
Day-7 analysis must parse BOTH streams:
- `mirror_events.log` → successful reverts (trigger=pin_drift) — the planned frequency table.
- `memory_mirror.log` → `pin_guard` arrays with `error:` entries → FAILED restores (new trigger class).
Combined, they give the true revert rate. Report failed-restores as a SEPARATE column: it is direct
evidence for a fix recommendation = **validate/repair canonical backups at pin-advance time** (so a
missing/wrong-sha backup can never silently defeat auto-repair). This strengthens Fix #2 beyond a mere
detection guard.

## Status
Evidence leaf only — goal #3 remains OPEN (acceptance still needs the one-week live dataset window 11-17→11-24).
This adds real in-window data + a new trigger class + a concrete day-7 parse requirement, all WITHOUT re-probing
the seed wall. Next checkpoint = 11-20 day-3 escalation if live events still 0.
