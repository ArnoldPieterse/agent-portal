# ANTI-STALL v2 - down_episode leak fix (2026-11-19)

## Bug
`_autoloop_watchdog()` pruned `down_streak` + `busy_ticks` on seat recovery but NOT `down_episode`.
Live evidence (memory/ops/autoloop.json): Researcher+Archivist had down_episode entries (reloads:2)
while down_streak={} (seats not down) -> stale episode state leaking across episodes.

## Consequences
1. Next outage starts with a stale `reloads` count -> premature/skipped escalation gates.
2. FATAL: a one-time `notified=True` survived forever -> the NEEDS-HUMAN last-resort line never
   re-fired for any future long outage of that seat (safety net defeated after first fire).

## Fix
agent_portal.py ~L3295: prune `episodes` for seats not in current `down` set (mirrors streaks/busy_ticks).

## Verification (in-sandbox, no :8888 needed)
Lifecycle test replicating exact logic:
OLD (buggy): {"a_notified": true, "a_reloads": 0, "stale_tracked_after_recovery": true, "b_notified": true}
NEW (fixed): {"a_notified": true, "a_reloads": 0, "stale_tracked_after_recovery": false, "b_notified": true}
Result: PASS
`python -m py_compile agent_portal.py` -> SYNTAX_OK (only pre-existing L303 docstring escape warning).
