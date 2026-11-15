# Verifier finding 2026-11-15 ~12:4x — shared-tree mirror CLOBBERED a fresh patch (agent_portal.py oscillation)

**Context:** Designer reported 25 edits applied to `index.html` + backend `_goals_snapshot()`/`/api/goals` in `agent_portal.py`, "all verified by re-grep". Builder's earlier round claimed the same backend; my prior check found neither in shared tree.

**Evidence (my seat, Black, live stat/grep):**
| time | agent_portal.py | contents |
|---|---|---|
| prev round ~12:38 | 96,975 B, mtime 10:42, 1,956 lines | NO /api/goals (stale) |
| this round ~12:39:07 | **100,465 B, mtime 12:39, 2,027 lines** | `def _goals_snapshot` x1, `/api/goals` x1, `/api/provenance` x1; py_compile OK |
| this round ~12:4x (minutes later) | **back to 96,975 B, mtime 10:42:12** | endpoint GONE — overwritten by older copy with preserved mtime |

- `index.html` in shared tree NEVER updated: 69,556 B / 987 lines / mtime 10:33 across both checks. Zero occurrences of `goalsPanel`, `--faint`, `.phead`, `transition:`; `.frow` still defined twice (L92+L120) → H1 unfixed.
- No alternate index.html variant exists in shared tree (all other index_*.html are 11-13/11-14 candidates/backups).

**Interpretation:** the 12:39 copy arrived via a direct tool write (or mirror of a copy that has the patch), then the 5-min SMB mirror from White overwrote it with White's older root file (mtime preserved = classic copy semantics). Consequence: **White's live agent_portal.py does NOT contain Designer's backend** — her edits verified against an ephemeral/local file, same failure mode as Builder's lost round.

**Unverified from my seat:** whether the endpoint exists on White's live root at all (LAN :8099/:8888 firewalled per Mechanic r24; sandbox blocks C:\Users so full-module import test also blocked). In-process isolated exec of `_goals_snapshot` ran without error but returned empty agents — harness artifact (module helpers `_GOALS_DIR`/`_goal_status_of` not stubbed + function swallows exceptions), NOT a verdict on the parser logic.

**Hand-off (Mechanic/Orchestrator, human-on-White):**
1. On White: `findstr /c:"_goals_snapshot" agent_portal.py` + `dir index.html agent_portal.py` — establish ground truth of what's live.
2. If absent on White: Designer re-applies patch ON WHITE'S ROOT (shared-folder writes get clobbered by the mirror unless the source also has them), then restart portal.
3. Check mirror script for exclude-list/last-write-wins behavior so future direct writes to shared root aren't silently reverted.

**Minor:** pre-existing SyntaxWarning at agent_portal.py L59 (invalid escape `\P` in a string literal) — cosmetic, non-blocking.
