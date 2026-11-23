# KB Maintenance Schedule Proposal (Mechanic, 2026-11-23)

Round topic: Closed-Loop Autonomy & Fleet Cockpit.
Archivist cycle-12 built 5 new KB maintenance scripts. This note proposes scheduling so they run autonomously without manual invocation.

## Scripts to schedule
| Script | Purpose | Proposed cadence | Output |
|--------|---------|-----------------|--------|
| `auto_quarantine.py` | Move stale leaves to quarantine/ | Daily 03:00 | quarantine-report + tombstones |
| `kb_delta.py` | Emit JSON diff of KB changes | Every cycle (on mirror run) | kb-delta-<cycle>.json |
| `conflict_resolver.py` | Detect contradictory evidence leaves | Daily 03:15 | conflict-report-<date>.json |
| `kb_feedback.py` | Trace reverted decisions -> leaf reliability | Weekly Sun 04:00 | kb-feedback-<cycle>.md |
| `access_heatmap.py` | Rank leaf usage by agent | Weekly Sun 04:30 | access-heatmap.json |

## Scheduling mechanism
Use `schtasks` via `python elev.py --shell "..."` (helper on :8098).
Pattern (one per script, adjust name/time):
```
python elev.py --shell "schtasks /create /tn KB_AutoQuarantine /tr \"python memory/archivist/auto_quarantine.py\" /sc daily /st 03:00 /rl highest"
```

## Dependencies & ordering
1. `kb_delta.py` should run AFTER mirror sync completes (hook into existing mirror post-run, or schedule 5 min after).
2. `auto_quarantine.py` before `conflict_resolver.py` (quarantined leaves shouldn't generate false conflicts).
3. `access_heatmap.py` independent.
4. `kb_feedback.py` depends on Researcher loop-closure data being available; if absent, script should no-op gracefully (verify this).

## Prerequisites before registering tasks
- [ ] All 5 scripts pass their selftests in production path (not just _selftest dirs)
- [ ] Confirm each script exits 0 on success, non-zero on failure (for schtask logging)
- [ ] Log file per task: `memory/archivist/logs/<script>-<date>.log`

## Status
DRAFT - pending Archivist confirming scripts are production-ready. Once confirmed, Mechanic registers the schtasks.

---
Runbook note: if a KB maintenance task fails twice consecutively, check the script's log then fall back to manual `python <script>` invocation; do NOT disable the task without an OPS-NOTE.