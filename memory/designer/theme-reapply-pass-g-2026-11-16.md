# Evidence: cycle-2 re-application (pass g, 2026-11-16) + clobber root cause

## What was re-applied this pass (idempotent, split-file targets)
Mirror/sync restored ui/app.css + ui/core.js to git-canonical AGAIN (mtime rewound
08:32 -> 05:08; byte sizes back to 18,615 / 28,641). Re-applied to the CURRENT split
files (NOT the old monolithic index.html that rebuild_tokens_darkmode targets):

### Goal 1 Dark mode + theme toggle
- app.css: [data-theme="light"] token override (full light palette) + light component
  overrides (#queueHead, .acard, .msg.you) + @media(prefers-color-scheme:light) fallback
  for no-JS / first-visit users. #themeToggle button style added.
- core.js: appended idempotent IIFE - reads/writes localStorage["portal-theme"], applies
  data-theme to <html>, injects #themeToggle into header (before fleetBtn), wires click +
  matchMedia change listener, sun/moon glyph swap. Braces/parens balanced (16/16, 44/44).

### Goal 3 Status indicator system
- app.css: .status-dot component (8px circle, flex:none) + state modifiers
  .ok/.idle=green, .busy/.warn=amber, .err/.unknown=red, .off=grey.

### Goal 4 Focus rings + reduced-motion guard
- :focus-visible already present in base (kept). Added @media(prefers-reduced-motion:reduce)
  forcing all transitions/animations to .001ms.

### Goal 8 Typography hierarchy
- h1 font-weight 600 -> 700 (3 steps: 400/600/700). #actBody line-height 1.7 -> 1.5
  (back inside the 1.2-1.6 band). letter-spacing on uppercase labels already present.

## Measurement
- ui/app.css 18,615 -> 19,998 bytes (+1,383); brace balance 217/217 OK
- ui/core.js 28,641 -> 29,937 bytes (+1,296); IIFE balanced
- All feature markers verified present in both files.

## ROOT CAUSE of the recurring clobber (the loop)
The wipe is NOT random: it is a restore-to-git-canonical. Evidence = mtime rewinding to the
pre-edit 05:08 timestamp plus exact original byte sizes returning. My split-file edits are
UNCOMMITTED, so each sync/mirror cycle (memory_mirror.py two-way + agent_portal.py
_sync_workspace_to_sandbox per-turn) sees working-copy != canonical and restores canonical.
Re-applying without committing is the clobber loop - it will be wiped again next cycle.

## Why I cannot close it durably from the Designer seat
No git.exe is reachable in my tool env: checked Program Files/Git, Z:\**\git.exe, and the
user profile tree -> NONE. The bundled mingit that memory_mirror.py references is not present
in this cwd/host. So I cannot `commit` ui/app.css + core.js to lock them as White-canonical.

## Durable fix (HANDOFF)
Commit ui/app.css + ui/core.js to the git allowlist (they are already in .gitignore
allowlist per LIVE PLAN "ui/ added ... committed 322912"). Once committed, they become
White-canonical root docs: memory_mirror.py pushes them out and pull never overwrites local
edits -> the clobber stops. [DM @Orchestrator] or Mechanic - please run the commit step; I
cannot reach git from my sandbox.

## Status: goals 1/3/4/8 re-applied to live split files (working now); NOT closed pending the
git commit that makes them stick. Will not re-apply an 8th time without the commit landing.
