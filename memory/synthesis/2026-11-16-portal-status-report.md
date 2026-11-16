# Portal developments — status report (2026-11-16, Scribe)

Requested by user. Every claim traces to a named on-disk source.

## 1. File-modularity rule + UI split (DONE, verified ~17:2x)
Source: TODO.md line 5; memory/portal/file-modularity.md; MEMORY.md 11-16 section.
- New fleet rule codified: working/project files follow memory/ index-pointer rules (small, modular, header pointers to parent) so small-context LLMs can apply changes. Canonical = memory/portal/file-modularity.md; standing rule in build_system_prompt.
- Root memory/INDEX.md trimmed 2435 -> 1395 chars (was over the 1600 _index_block budget; tail was silently truncated from every prompt).
- First split DONE: index.html 91 KB -> markup-only shell 10.3 KB + ui/app.css (18.6) + ui/core.js (28.6) + ui/uploads.js (33.5). GET /ui/* route added (basename+ext whitelist, no traversal).
- Pin advanced e0679e5f0844 -> 10bbd8ddf982 same-turn; backup memory/designer/index_html_CANONICAL_10bbd8ddf982_2026-11-16h.html; ui/ added to .gitignore allowlist; committed 3229126.
- VERIFY after restart: GET /ui/* -> 200 correct Content-Type (18615/28641/33513 bytes); traversal ..%5C blocked 404; module contents byte-identical to original inline blocks, load order preserved.

## 2. Goal-stall loop fix (FIXED, verified unit + endpoint)
Source: memory/portal/bugs/goal-stall-loop-2026-11-16.md.
Three compounding root causes:
1. _agent_goals_block listed CLOSED goals as open (naive regex, no marker check) -> agents re-verified finished work every turn.
2. Sandbox clobber loop: push-only edits overwritten by next HERE->sandbox push; index.html additionally pinned by PIN_GUARD -> edit-revert-edit forever.
3. Evidence never registered: real progress in lane files/chat, not as (verified:) markers the dashboard counts; sweep only matched .md leaves.
Fixes:
- _agent_goals_block now uses strict ledger parsing + spells out CLOSURE PROCEDURE; budget 1400->1800 chars.
- Sandbox merge queue: _merge_queue_scan() snapshots diverged push-only files before clobber (memory/ops/merge-queue/); GET /api/merge-queue + POST /api/merge restore; Ops panel one-click. Lost work now recoverable.
- sweep_evidence extended to .py/.jsonl/.json/.html/.css (not just .md). First run auto-linked Builder#1 + Designer#1.
- Git-based goal progress: GET /api/goals/history reads 8 goal files at recent commits, counts marker lines = true reached per checkpoint; stall_commits = consecutive no-change. Cached 30 s/HEAD.
- PIN GUARD made legible to agents (repin procedure in TOOLS prompt block).
- _git() hardened: lenient utf-8 decode + max_out param (default 8 KB cap was truncating diffs).

## 3. Git safety net (DONE)
Source: TODO.md line 7; MEMORY.md 11-16 section.
- PortalDailyGitCommit daily 18:00 -> every 15 min (no-op when clean; first live run committed 4fcba3f). Per-turn _auto_commit unchanged => drift <= 1 turn in chat, <= 15 min idle.

## 4. Goals "blocked" false-positive fix (DONE)
Source: TODO.md line 6.
- _goals_snapshot now counts only explicit "(blocked: ...)" / [BLOCKED] markers (Mechanic cycle-2 #6 prose was the 1-blocked artifact). Standing rule teaches agents the marker form.

## 5. Earlier portal work (2026-11-15)
Source: memory/portal/bugs/INDEX.md.
- popup-pythonw fix: CREATE_NO_WINDOW on all pythonw children + RecoverAll task via recover_hidden.vbs.
- file-links-sandbox: dual-root resolver, env fix, exact-path echo, real Content-Type; /api/file/raw serves correct MIME (.html renders).
- Prune edge cases tested + live e2e (110 lines pruned, no chunk due).

## Current open items / concerns
- **Portal DOWN on White :8099** (MEMORY.md hot note, root cause truncated). This is the most recent state line.
- Mirror clobber #3: cycle-2 design work wiped again; re-applied to ui/app.css + ui/core.js, design_check passes 0 violations.
- SPLIT PENDING: agent_portal.py ~173 KB -> modules under single importable entry (PortalRun task must keep working); TODO.md prune via POST /api/todo/prune (145 KB -> completed sections to TODO_completed.md).
- Fleet cycle-2 at 22/80 (27.5%) per MEMORY.md goal line; Archivist lane complete 10/10.

## Supersession note
This report is a point-in-time snapshot, not a supersession of any prior synthesis leaf. The goal-stall-loop fix supersedes the earlier "dashboard stuck" symptom descriptions in chat but does not replace the bug leaf itself (which remains the canonical record).