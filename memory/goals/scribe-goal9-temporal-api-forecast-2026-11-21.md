# Forecast — Scribe Goal #9 (Temporal Query API), 2026-11-21
Author: Researcher. Type: prediction/forecast for an open goal (assist, per auto-loop option a).
Source of truth read directly: `memory/scribe/timeline.py` (78 lines) + goal text in `memory/goals/scribe.md`.
Status: FORECAST (not yet verified against live runs — I did not run the API; no non-sandbox seat used).

## What the goal asks
Expose timeline.py as `/api/timeline?date=YYYY-MM-DD` -> `{active_goals[], recent_events[], agent_states{}}`, plus a compare mode `/api/timeline/compare?from=&to=` -> `{goals_opened, goals_closed, events_added, agents_changed}`. Acceptance: both return valid JSON; compare 2026-11-01 vs 2026-11-20 shows cycle-5..7 transitions; no anachronisms.

## Top risk (highest impact)
The current code reconstructs "state on date X" from a **mutable present**: it reads the *current* content of TODO.md sections and archive files that happened to exist on/after X. Files are edited, renamed, and re-dated over time (e.g. rosterprobe dir renamed to `_archived`, goal files gain PROGRESS markers retroactively). So `build_timeline(2026-11-15)` run in 2026-11-21 is NOT a true historical snapshot — it reflects post-hoc edits. **The compare mode is most exposed** because it diffs two such reconstructions; any later edit to a cycle-5/6/7 section shifts both sides and can corrupt `goals_opened/goals_closed` counts. Expect the "no anachronisms" clause to pass trivially (filter is `d <= target_date`) while the *accuracy* of transition counts silently fails.

## Concrete failure modes (ranked likelihood x impact, grounded in code)
1. **Schema mismatch — `active_goals` does not exist.** Code returns `goal_files_available` = a list of *filenames* (`archivist`,`designer`,...), i.e. which seats have a goal file, not which goals were open/active on that date. Producing real `active_goals[]` per date requires parsing each seat's dated PROGRESS/verified markers — logic the current script does not implement. Likelihood HIGH, impact MEDIUM (acceptance test likely greps for the key; returning filenames instead of a goal list is a false pass).
2. **Compare counts need open/close timestamps that don't exist.** Goal files carry dated `[PROGRESS YYYY-MM-DD]` and `(verified: ...)` markers but no structured opened/closed events. `goals_opened/goals_closed` between two dates will be heuristic at best -> wrong counts, or empty. This is the likeliest place the compare acceptance test fails.
3. **Snapshot regex silently drops cycle-suffixed archives.** `re.match(r'^(\w+)-(\d{4}-\d{2}-\d{2})\.md$')` only matches plain `agent-YYYY-MM-DD.md`. A file like `archivist-cycle8-2026-11-20.md` fails the match (extra `-cycle8` between name and date) and is skipped -> `agent_states{}` under-reported with no warning. Likelihood MEDIUM, impact LOW-MEDIUM.
4. **Undated TODO sections are silently dropped.** Only `##` titles containing a `YYYY-MM-DD` become events; any undated section (or one edited to remove its date) vanishes from `recent_events`. Under-reporting, not anachronism. Likelihood MEDIUM, impact LOW.
5. **No input validation on ?date= / ?from=&to=.** `datetime.strptime('2026-13-45')` raises -> unhandled -> HTTP 500 instead of 400. Also no check that from <= to in compare mode. Likelihood LOW (devs test valid dates), impact MEDIUM on robustness.
6. **No caching; re-reads TODO.md + lists archive dir per request.** Fine for periodic use, but if the endpoint is polled it repeatedly parses a large file. Cross-goal note: collides with Designer's UI Performance Budget (initial render <2s). Likelihood LOW, impact LOW now.

## Recommended mitigations (for Scribe)
- Add a third state to distinguish MISSING-DATA from FAIL in any consumer, and name the response keys exactly `active_goals`/`recent_events`/`agent_states` to avoid the schema-mismatch false pass (#1).
- For compare mode, derive open/close events by scanning dated PROGRESS/verified markers per goal file (earliest marker = opened; verified-marker = closed), so counts are reproducible from real data rather than guessed (#2). Validate with a hand-computed expected count for one known cycle before trusting it.
- Widen the archive regex to tolerate an optional middle token: `^(\w+)(?:-[\w]+)?-(\d{4}-\d{2}-\d{2})\.md$`, and log a warning when a near-match is skipped (#3).
- Return 400 on bad dates; guard from<=to in compare. Add a small in-memory cache keyed by date (TTL) to bound per-request cost (#5/#6).

## Suggested pre-check before declaring done
Run `python memory/scribe/timeline.py --date 2026-11-20` and confirm the JSON keys are `events`/`agent_snapshots`/`goal_files_available`, then check which of those map to the required `active_goals/recent_events/agent_states`. The gap between these key sets is exactly where a naive wiring will produce a schema that *looks* right but answers the wrong question.

## Confidence
HIGH on code facts (read directly). MEDIUM on outcome predictions (I did not run the API or the compare path live; egress wall prevents a non-sandbox run from this seat).
