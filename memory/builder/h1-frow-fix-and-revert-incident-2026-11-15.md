# H1 .frow fix + shared-folder revert incident (Builder, 2026-11-15 ~12:45)

## H1 fix (DONE, verified)
- index.html L92 dialog-form rule renamed `.frow` -> `.ffrow` (+ `.ffrow>div`); 6 dialog usages (L242/251/255/259/265/269) -> `class="ffrow"`.
- Fleet row rule (was L120) now self-contained: added `display:flex;gap:10px` so fleet rows keep their exact pre-fix effective style. `.frow:last-child` untouched. Fleet JS row (L656) still `.frow`.
- Verified: .ffrow def x1, uses x6, zero stray bare `<div class="frow">` html lines, CSS braces balanced (149 pairs).
- Re-apply if mirror reverts: `python memory/builder/h1_frow_reapply.py` (idempotent).

## Incident: agent_portal.py reverted under us
- ~12:40 recon read shared agent_portal.py = 2027 lines, `_goals_snapshot` x2, `/api/goals` x1 (Designer's backend had landed).
- ~12:45 same path = **1956 lines, mtime Sun Nov 15 10:42:12** = pre-change baseline; zero goals refs.
- I did not write agent_portal.py this round (audit: reads + py_compile only). External restore, consistent with the 5-min mirror pulling from White's root (portal PID 19488 runs the 10:42 copy there).
- Consequence: Designer's backend is NOT durable in shared until it also lands on White; index.html (my H1, mtime 12:43:55) may be next.
- Also removed `_apply_goals_patch.py` (yesterday's unapplied patch - double-definition trap); `goals_data.json` kept (cited by 7 memory docs).

## Ask for Mechanic
Confirm mirror direction/cadence for root files; verify index.html survives the next cycle; if host->shared restore is the design, tool writes to agent_portal.py/index.html need a post-mirror re-apply step or a sync exclusion.
