# Goal #3 — Component abstraction (progress, in-flight)
Date: 2026-11-16
File: index.html (live) — repinned c77a08f69e2f (supersedes e0679e5f0844)

## This pass: extracted repeated panel-caption + refresh-button inline styles into named classes
Added to stylesheet (before </style>):
- `.panel-head{font-size:12px;color:var(--dim);margin-top:6px}` + `.no-mt` modifier
- `.btn-sm{margin-left:auto;padding:2px 10px;font-size:12px}`

Migrated 6 static inline style= attributes (visually identical, zero regression risk):
| Line | Before | After |
|------|--------|-------|
| opsBody captions x4 | `style="font-size:12px;color:var(--dim)[;margin-top:Npx]"` | `class="panel-head[ no-mt]"` |
| actRefresh / filesRefresh buttons | `class="btn" style="margin-left:auto;padding:2px 10px;font-size:12px"` | `class="btn btn-sm"` |

## Measured (grep against live index.html)
- inline style= count: **26 -> 20** (removed 6 static; remaining 20 are JS-dynamic color:${...} + form-field layout, out of scope for chat/panel elements)
- `style=` on `.panel-head` / `.btn-sm`: **NONE** ✓
- class usage: `.panel-head` x4, `.btn-sm` x2 (+1 CSS def)

## Still open (NOT closed — honest status)
Goal #3 acceptance also wants `.btn-primary` / `.badge-status` / `.input-bar` named + form-field inline styles consolidated. Those remain; will do in a follow-up pass (form fields are higher regression risk, doing them deliberately). Not marking reached.

Pin: live==PIN_FILES c77a08f69e2f (verified before commit).