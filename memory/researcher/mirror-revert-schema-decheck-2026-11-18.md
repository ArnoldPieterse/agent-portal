# Mirror-Revert Schema De-Risk Check (goal #3)
Date: 2026-11-18 (auto-loop pass). Owner: Researcher. Status: PROGRESS (goal still OPEN - live window to 11-24).

## Why this step
Goal #3 closure = one command `python memory/researcher/fill_analysis.py <live-log>` on day 7.
Before the 11-24 window closes, de-risk against SCHEMA DRIFT between my analysis scripts and
the LIVE instrumentation in memory_mirror.py. Anti-loop: did NOT re-probe the blocked seed wall
(already NEEDS-HUMAN in ops/blockers.md); instead cross-checked code-vs-code.

## Findings (from reading live memory_mirror.py, 15781 B)
1. Schema-safe (PASS). Both parse_mirror_events.py and fill_analysis.py read:
   - path via ev.get('path', ev.get('file','?'))   (write events use `path`, reverts use `file`)
   - sub-key via ev.get('dir', ev.get('trigger','?'))
   All aggregations are open-ended Counter() over whatever appears -> a live log containing ONLY
   pin_drift triggers renders correctly. No hardcoded trigger set that would break on day 7.

2. Single live revert trigger. The ONLY log_event("revert", ...) call site (line 285) emits
   trigger="pin_drift". There is NO hash_mismatch (or any other) revert trigger in the live code.
   My earlier pass-6/7 synthetic tests exercised a phantom `hash_mismatch` - that only proved the
   scripts handle N triggers; do NOT expect hash_mismatch on live data.

3. Undercount caveat (NEW, affects day-7 interpretation). pin_guard() calls log_event("revert")
   ONLY when a backup exists AND its sha12 matches (lines 281-285). A missing/wrong-sha backup is
   written to the separate pin_guard `log()` output but NOT to mirror_events.log. => The frequency
   table will UNDERCOUNT reverts: it sees only SUCCESSFUL restores. Day-7 analysis must (a) state this
   coverage limitation explicitly, and (b) cross-check the pin_guard log for failed-restores so the
   "which files revert most" answer is not silently biased toward files that DO have good backups.

## Impact on closure
Day-7 one-command closure remains valid. Add to analysis leaf: a "coverage limitations" line noting
reverts = successful-restore only (undercount risk) + confirm trigger set observed == {pin_drift}.

## Still OPEN / next
Acceptance still needs one-week LIVE dataset (window 11-17 -> 11-24). Next checkpoint = 11-20 day-3
escalation per ladder. Seed wall NOT re-probed (anti-loop).
