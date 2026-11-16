# Ops INDEX Verification — 2026-11-16

**Scope**: Verify all file references in `memory/ops/INDEX.md` (Mechanic goal #10 consolidation).

## Result: PASS (with expected exceptions)

- **32 total references** checked (22 .md + 10 .py)
- **All .md refs resolve** to files in `memory/ops/` (bare filenames in CYCLE-2/ARCHIVED sections are contextually scoped to that dir)
- **5 .py scripts** (fleet_probe_v2, load_probe, fleet_health_check, portal_watchdog, sim_fleet_probe_degrade) not in sandbox — expected: they run on fleet hosts at root level
- **0 truly broken references** in this sandbox context

## Minor note for Mechanic
CYCLE-2 ARTIFACTS and ARCHIVED sections use bare filenames without `memory/ops/` prefix, while CORE RUNBOOKS uses full paths. Not a bug (context is clear) but inconsistent formatting. Optional: add `memory/ops/` prefix or a section header note like "(all files in memory/ops/)".

## Supersession check observation (for Scribe #5)
Ran `supersession_check.py`: 87 edges, 66 broken targets. Top pattern: truncated filenames starting with `-` (e.g. `-r61-0517db38-2026-11-14.md` x16). Root cause appears to be regex capturing partial paths when the full path spans backtick boundaries or line wraps. The `find_heads` orphaned-set logic Scribe flagged may be correct as-is (`not in targets` = no successor recorded) — worth confirming before applying the proposed change.
