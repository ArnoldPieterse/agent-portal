# RUNBOOK: sandbox merge queue + git goal-progress tracking (2026-11-16)

Owner: Mechanic (ops) / Builder (tooling). Live since portal restart 2026-11-16.
Context: memory/portal/bugs/goal-stall-loop-2026-11-16.md (why this exists).

## 1. Sandbox merge queue (recover agent code edits before push-clobber)
Agent tools run in Studio's `_default` sandbox. Edits to git-allowlisted code/config files there
are push-only and were silently destroyed by the next HERE->sandbox push. Now:
- Every sync runs `_merge_queue_scan()` FIRST: any diverged allowlisted file is snapshotted to
  `memory/ops/merge-queue/<file>.<sha10>` + one jsonl event in `memory/ops/merge-queue.jsonl`
  (deduped per file+content). Both live under memory/ -> auto-committed, never lost.
- **UI**: Ops panel -> "Sandbox merge queue" box: last 5 events with sha/size + one-click
  **↩ restore** (POST /api/merge {file} [sha]) = copy snapshot onto root + git commit
  "merge: <file> restored from sandbox snapshot <name>". Only git-allowlisted files restorable.
- **API**: GET /api/merge-queue -> {events[40 newest first], snapshots[]}; POST /api/merge.
- Routine: after any portal restart or big ops edit, glance at the queue - if an agent's pending
  edit was captured, restore it (or tell the owning agent to re-apply on top of the snapshot).

## 2. Git-based goal progress (goals ARE registered in git)
memory/goals/*.md is tracked + auto-committed every turn (post-turn sync + 15-min safety net since 2026-11-16), so
git history IS the goal-progress record:
- **GET /api/goals/history**: checkpoints = recent commits touching memory/goals/ (thinned to 8);
  at each, the 8 agent files are read from that commit and marker-bearing goal lines counted
  (true reached count; NOT diff arithmetic - rewrites net to zero). Plus stall_commits (consecutive
  recent commits with no goal-file change) + last_change_commit. Cached 30 s per HEAD.
- **UI**: Goals panel, under the rings: "git progress (last N commits): a → b → … → cur/80 ·
  last goal change <sha> <ts>" + "⚠ stalled: K commits since last goal change" when K > 3.
- Reading the curve: a flat line with rising stall_commits = fleet spinning without registering
  progress (the 2026-11-16 symptom, now visible). A step down = cycle reset (new goal set).

## 3. Closing goals (the only thing that moves the dashboard)
Chat claims do NOT count. A goal counts when its line in memory/goals/<agent>.md carries a marker:
1. Direct: `python memory/researcher/goal_ledger.py --record <agent> <goal#> --note '<what ran + artifact path>'`
   (appends `(verified: date - note)`; also accepts `--leaf RELPATH` for a validated pointer).
2. Sweep: write an evidence leaf in memory/<agent>/ AND add a line to that lane's INDEX.md;
   the end-of-run sweep auto-appends `(pointer: <leaf>)`. Since 2026-11-16 artifacts (.py etc.)
   count too, not just .md leaves. Pointers require index linkage - dangling ones never count.
3. The per-turn prompt now tells every agent exactly this (CLOSURE PROCEDURE block).

## 4. Pinning index.html (stop the clobber loop)
index.html is pinned in memory_mirror.py PIN_FILES; any deviation is restored on the next mirror
cycle. To LAND a change: edit -> `sha12 = sha1(file)[:12]` -> copy to
memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html -> update PIN_FILES (sha12 + backup)
-> commit. Agents are told this in the TOOLS prompt block (PINNED FILES note). Lineage:
df1bbdaef684 -> ac3ca7a6a264 -> 2c6399f2d853 -> e0679e5f0844 (this runbook's UI, 2026-11-16d).

## Verified (2026-11-16)
Unit: scan/idempotency/status/restore + allowlist rejections (isolated temp repo); history curve
0->7->49->52->60->66 (cycle 1) -> 5 (reset) -> 21 (live ~22). Live endpoints verified post-restart.
