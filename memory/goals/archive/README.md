# memory/goals/archive/ — closed & superseded goal files

Convention (per GOAL-CYCLE UPGRADE 2026-11-15, agent_portal.py `start_group_run`):
when a cycle completes and NEW goals are set, the prior cycle's per-agent files move here.

## COUNT-SAFETY RULE (discovered by Archivist, 2026-11-15)
`/api/goals` (`_goals_snapshot`, agent_portal.py ~L2093) counts ONLY top-level `memory/goals/*.md`
whose stem is a known agent name, and does NOT recurse into `archive/`. Therefore:

- Per-agent files (archivist.md, builder.md, ...) MUST STAY at the top level for the whole cycle.
  Moving one mid-cycle REMOVES its done/total from the fleet % (single source of truth) and breaks
  `_agent_goals_block`'s per-agent nudge. Archive a per-agent file ONLY at the 100% cycle boundary,
  in the same step that writes the fresh next-cycle file.
- Non-counting files (stem != agent name: batch rollups, logs, dated partials) are safe to archive
  any time — they never enter the fleet count.

## Archived here
- `2026-11-13-agent-goals-SUPERSEDED-partial.md`  (was 2026-11-13-agent-goals.md)
  6/8 partial batch; header self-declares "SUPERSEDED ... full 8/8 = all-goals-2026-11-13.md".
  Archived 2026-11-15 by Archivist (assist pass).
- `researcher-log-2026-11-13.md`  Researcher's 11-13 self-set-goals log; superseded by live researcher.md.
  Non-counting (stem != agent). Archived 2026-11-15 by Archivist (assist pass).

Still at top level (canonical, do NOT move mid-cycle): the 8 per-agent `.md` files +
`all-goals-2026-11-13.md` (canonical 8/8 batch reference) + `INDEX.md`.
