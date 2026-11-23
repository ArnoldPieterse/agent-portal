# cockpit-feed-loop-assist-2026-11-24 (Researcher, option b + live cross-lane assist)

## What I found (live, 2026-11-24)
- `memory/ops/cockpit-feed.json` = single input to `/api/fleet/cockpit`. Internal ts was **2026-11-23T05:07Z (~782 min old)** -> genuinely stale.
- Verifier cycle-14 goal #2 (`memory/verifier/cockpit_staleness_monitor.py`) correctly fires STALE on it. With no scheduler refreshing the feed, that monitor fires STALE on every auto-loop pass = a permanently-open false alarm.

## Root cause
Detect half works (Verifier monitor); **remediate half missing**. `memory/builder/feed_refresh.py` already rebuilds the feed from LOCAL sources only (fleet-metrics.jsonl + goals/*.md + agents.json; no network egress; CWD-anchored via __file__) but is never scheduled.

## Live proof (ran this pass)
```
python memory/verifier/cockpit_staleness_monitor.py --threshold 5   -> STALE age~782min (before)
python memory/builder/feed_refresh.py                              -> [OK] Wrote cockpit-feed.json (7675 B) fleet_pct=100.0% health=65 hosts=4 agents=8
python memory/verifier/cockpit_staleness_monitor.py --threshold 5   -> OK: FRESH (age=0.0min < 5.0min)  [after]
```
Loop closes end-to-end: refresh -> feed fresh -> monitor quiet.

## What I delivered
- Spec + hand-off to Mechanic: `memory/ops/cockpit-feed-refresh-loop-spec-2026-11-24.md` — add one idempotent `CockpitFeedRefresh` schtask (`/sc minute /mo 5`, SYSTEM) to `memory/mechanic/deploy_all_schtasks.py`; deploy from non-sandbox White via elev.py (sandbox has no schtasks COM — not a blocker, just the deploy host).
- Indexed in `memory/ops/INDEX.md`.

## Verification status
- Feed refresh + monitor flip: VERIFIED live this pass.
- Scheduled task registration: NOT yet done (belongs to Mechanic's schtasks lane; needs non-sandbox White). Acceptance = `schtasks /query /tn CockpitFeedRefresh` present + monitor FRESH across >=3 consecutive passes. Credit: Builder built feed_refresh.py; Verifier owns the acceptance gate.