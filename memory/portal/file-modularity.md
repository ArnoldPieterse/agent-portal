# File modularity rule — working/project files (2026-11-16, user directive)

Last updated: 2026-11-16. Canonical for the fleet rule: **working files and project files
follow the SAME rules as the memory/ index-pointer system** — keep every file small/minimal,
use pointers and references to parent files, ultimate modularization. Goal: a small-context
LLM must be able to read ONE file whole and apply a change without loading megabytes.

## The rule (applies to code/config/UI, not just memory/)
1. One concern per file. If a file mixes concerns (markup+styles+logic), split it into modules.
2. Every module carries a HEADER POINTER block: what it is, its parent, its siblings, the rule
   doc (this file), and how it is served/consumed. Copy the ui/app.css header as the template.
3. Size budgets (soft; exceeding = split candidate, logged in TODO.md top section):
   - index.html  <= ~12 KB (markup-only shell) — UI lives in ui/*.css / ui/*.js
   - agent_portal.py  <= ~100 KB per module; >150 KB = must-split (currently 173 KB, SPLIT PENDING)
   - any .py/.js/.css working file  <= ~40 KB without a documented reason in its header
   - memory/ leaves: unchanged rules (root INDEX < 1600 chars; MEMORY.md < ~2 KB)
4. Pointers beat copies: reference the parent/sibling by relative path instead of duplicating
   content (same as memory/ INDEX convention `-> path  summary`).
5. After any split: update every pointer that referenced the old monolith (grep for the file
   name across memory/, TODO.md, agents' goal evidence), then commit.

## Split procedure (proven on index.html, 2026-11-16)
1. Extract blocks into new files under a dedicated dir (ui/); add header pointers; keep load order.
2. Replace blocks in the parent with references (`<link>`, `<script src=...>`).
3. If the parent is PINNED (memory_mirror.py PIN_FILES): create canonical backup
   `memory/designer/index_html_CANONICAL_<sha12>_2026-11-16x.html` AND update PIN_FILES in the
   SAME turn — pin_guard reverts any un-pinned edit within one mirror cycle (~5 min). Observed live.
4. New files need no allowlist work: sync + git use `git ls-files`, so `git add` covers them.
5. Server-side: new static dirs need a route (GET /ui/* added to agent_portal.py do_GET,
   basename+extension whitelist, no traversal) — then RESTART per ops/windows-runbook.md
   (taskkill PID first; bare schtasks /run no-ops).
6. Verify: GET each module URL returns 200 + right Content-Type; browser hard-refresh renders;
   run the portal smoke (GET /api/memory, /api/goals) after restart.

## Current inventory (2026-11-16, after first split)
- index.html  10.3 KB shell -> ui/app.css 18.6 KB + ui/core.js 28.6 KB + ui/uploads.js 33.5 KB  DONE
- agent_portal.py  ~173 KB / ~3500 lines  SPLIT PENDING (candidate seams: git+merge-queue ops,
  goals/ledger, fleet/probe, sync/mirror, chat loop — one module file each under portal_modules/?
  decide in cycle 2; must keep a single importable entry for the PortalRun task)
- TODO.md  ~145 KB  PRUNE PENDING (run POST /api/todo/prune; completed sections -> TODO_completed.md)
- agents.json ~9.5 KB, goal_ledger.py ~9 KB, daily_git_commit.py <2 KB  OK

## Pointers
- pin mechanics + revert evidence -> memory_mirror.py PIN_FILES + memory_mirror.log (pin_guard lines)
- restart trap -> memory/ops/windows-runbook.md
- mirror clobber context -> memory/portal/mirror-clobber-pattern-2026-11-14.md
- git allowlist = `git ls-files` (curated .gitignore) -> memory/portal/architecture.md (OPS section)
