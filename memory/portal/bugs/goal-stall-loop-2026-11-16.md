# BUG: goal-stall loop - agents repeat work, progress invisible (2026-11-16)

Status: **FIXED 2026-11-16** (code live after portal restart; verified unit + endpoint).
Reported by user: fleet dashboard stuck at ~20/80 while agents visibly "work" every turn.

## Symptom
Dashboard 0-20% for most seats despite real artifacts on disk; chat shows the same pattern
every turn: claim DONE -> Verifier flags artifact missing -> re-audit -> re-apply -> repeat.

## Root causes (three, compounding)
1. **`_agent_goals_block` listed CLOSED goals as open.** Naive regex matched every numbered
   line; it never checked for the `(verified:)`/`(pointer:)` marker the strict ledger requires.
   Every turn's "YOUR OPEN GOALS" nudge re-listed finished work -> agents started each turn by
   re-verifying completed goals (the visible repetition loop).
2. **Sandbox clobber loop.** Agent tools run in Studio's `_default` sandbox; edits to code/config
   files there are push-only (never pulled back) and get silently overwritten by the next
   HERE->sandbox push. index.html is additionally pinned by memory_mirror.py PIN_GUARD - any
   deviation is restored from the canonical backup on every mirror cycle. Designer's whole
cycle-2 goal set is index.html work: edit -> reverted -> re-edit, forever. Observed live 2026-11-16:
   a frontend edit to index.html was reverted by PIN_GUARD within one mirror cycle.
3. **Evidence never registered.** Real progress landed in lane files/chat, not as markers on the
   goal lines in memory/goals/<agent>.md that the dashboard counts. The end-of-run evidence sweep
   only matched `.md` leaves - Builder's actual artifacts are `.py` scripts, so they could never
count even when index-linked.

## Fixes (2026-11-16)
- `_agent_goals_block` now parses with the strict ledger (only truly-open goals listed, reached
  count shown) and spells out the CLOSURE PROCEDURE: `python memory/researcher/goal_ledger.py
  --record <you> <goal#> --note '<what ran + artifact path>'`, or evidence leaf + INDEX line for
  the sweep to auto-link. Budget raised 1400->1800 chars (team rules were being truncated away).
- **Sandbox merge queue**: `_merge_queue_scan()` runs at the top of every sync and snapshots any
  diverged push-only file BEFORE the clobber (memory/ops/merge-queue/<file>.<sha> +
  memory/ops/merge-queue.jsonl, both git-tracked). GET /api/merge-queue lists events;
  POST /api/merge {file} restores a snapshot onto the root and commits. Ops panel shows the queue
  with one-click restore. Lost work is now recoverable instead of silent.
- `sweep_evidence` (memory/researcher/goal_ledger.py) now also matches index-linked artifacts
  (.py/.jsonl/.json/.html/.css), not just .md leaves. First run auto-linked Builder#1 ->
  memory/builder/pre_commit_gate.py and Designer#1 -> apply_designer_scale_patch.py.
- **Git-based goal progress**: GET /api/goals/history - goals ARE registered in git (memory/goals/*.md
  tracked + auto-committed per turn); the endpoint reads the 8 goal files at recent goal-touching
  commits (`git show`) and counts marker lines = true reached count per checkpoint (diff arithmetic
  was tried first and is unreliable: rewrite commits net to zero, two different commit sets,
  truncation). stall_commits = consecutive recent commits with no goal-file change. Cached 30 s
  per HEAD. Goals panel renders the curve + stall warning.
- **PIN GUARD made legible to agents**: TOOLS prompt block now documents the repin procedure
  (backup copy memory/designer/index_html_CANONICAL_<sha12>_...html + advance PIN_FILES in
  memory_mirror.py) so index.html work lands instead of looping. Pin advanced to e0679e5f0844
  (2026-11-16d) for this fix's UI.
- `_git()` hardened: lenient utf-8 decode (git log -p on tracked binaries crashed the reader
  thread, losing the whole result) + max_out parameter (default 8 KB cap silently truncated
  goal-file rewrite diffs).

## Verified
- py_compile agent_portal.py + goal_ledger.py PASS; unit tests: closed-goal filtering (orchestrator
  shows 8/10 reached, only 2 truly open listed), merge-queue scan/idempotency/status/restore +
  allowlist security rejections in isolated temp dirs, _goals_history curve 0->7->49->52->60->66
  (cycle 1) -> 5 (cycle-2 reset) -> 21 (live 22-23).
- Sweep idempotent: second run writes nothing.
- Live endpoint verification after restart: /api/goals, /api/goals/history, /api/merge-queue.

## Related
- memory/ops/merge-queue-git-progress-2026-11-16.md (runbook)
- memory/designer/INDEX.md (pin backup lineage 2c6399f2d853 -> e0679e5f0844)
