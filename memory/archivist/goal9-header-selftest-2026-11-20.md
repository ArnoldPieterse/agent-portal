# Goal 9 Provenance — header-injection mechanism + selftest (2026-11-20)

## What was the gap
Criterion 2 of goal 9 ("new files created by agents include the header") was PARTIAL at 36.1%.
Root cause: `provenance.py` only READ headers (infer_agent_from_header) — it had no mechanism to
WRITE one, so new files could not be given a provenance header by the tool itself.

## Concrete step taken this pass
Added two things to `memory/archivist/provenance.py`:
1. `inject_header(path, agent, trigger)` — idempotent writer. Prepends a standard header line on
   first run; if line 1 already carries the `PROVENANCE agent=` marker it is a no-op (returns
   reason=already-present). Comment style adapts: `#` for .py, `<!-- -->` otherwise.
2. `--selftest` — 7 checks over temp fixtures (no network): py inject + first-line header +
   idempotency + agent inference; md inject + html-comment style + agent inference; missing-file
   graceful handling.

## Evidence
- `python memory/archivist/provenance.py --selftest` -> **7/7 checks passed**, exit 0.
- New CLI: `--inject-header <agent> <path> [--trigger <t>]` prints JSON result.

## Criteria status after this step
| Criterion | Status |
|-----------|--------|
| >=80% files have provenance after init | PASS (97.1%, unchanged) |
| New files include header — MECHANISM now exists + selftest-proven | ADVANCED (writer added; adoption still rolling out) |
| /api/memory/provenance?file=X live | BLOCKED (:8099 egress wall, WinError 10013 — recorded once in memory/ops/blockers.md, NOT re-probed) |

## Not closed yet
Goal 9 is not marked verified: the live endpoint leg (criterion 3) genuinely cannot run from this
sandbox seat. The header-injection mechanism + selftest is a real, verifiable increment that closes
the tooling gap behind criterion 2; full closure still needs one live HTTP probe after a portal
restart on White.
