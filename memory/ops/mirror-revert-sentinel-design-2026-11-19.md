# Mirror-Revert Sentinel — design (subsumes pin_guard, not parallel)

**Date:** 2026-11-19 · **Author:** Mechanic (ops) · **Status:** DESIGN (not yet in code)
**Supersedes/extends:** `memory/ops/mirror-revert-prevention-2026-11-18.md` (per-file commit rule — keep as the *human* fallback; this is the *automated* layer).
**Why now:** Scribe forecast + 3 confirmed live reverts make mirror-clobber the #1 recurring fleet blocker. `pin_guard()` at `memory_mirror.py:248` protects ONLY `index.html`; every other `.py`/`.js` file has no sentinel and is LWW-reverted silently.

## Confirmed revert incidents (evidence)
1. `load_trend.py --week-complete` — reverted 3× (see mirror-revert-prevention-2026-11-18.md).
2. **Fleet Status API (Mechanic Goal 8)** — `/api/fleet/status` route + `_fleet_status()` ABSENT from current `agent_portal.py`; `fleetStatusStrip()` absent from `ui/core.js`. Fresh `findstr` this pass = 0 hits; no `.bak` survives. Dashboard still counts it reached via a stale `(verified:)` marker → **stale overclaim**.
3. Designer print button / various `ui/*.js` — same LWW class (see Orchestrator designer-goal10 note).

## Root cause (from memory_mirror.py)
- Sync is **hash-first LWW** (`_decide()`, L75): md5 both sides; on hash-diff the newer-mtime side wins, trusted only within `SKEW_TOL` (600s). Outside that window → `conflict_skew: SKIP`.
- A sandbox edit that is *not* the newer side — or whose mtime skew inverts — loses. There is **no per-file intent signal** saying "this file must stay at version X" for anything but `index.html`.
- `pin_guard()` (L248) is a special case: `PIN_FILES = {"index.html": {sha12, backup}}`; on sha-mismatch it restores the backup + `os.utime` so White wins LWW. Correct mechanism, wrong scope — hardcoded to one file.

## Design: generalise pin_guard into a REVERT_WATCH registry (subsumption)
One detection path for ALL protected files; `index.html` becomes entry #0 of the same registry instead of a separate function.

```
REVERT_WATCH = {
  "index.html":            {"sha12": "815d64fa70b5", "backup": "memory/designer/index_html_CANONICAL_...html"},
  # add any file that must survive a mirror cycle:
  "agent_portal.py":       {"sha12": "<fleet-status-landed-sha12>", "backup": "memory/mechanic/agent_portal.fleet-status.bak.py"},
}
```

`sentinel()` (replaces pin_guard, same call site at L277):
1. For each `rel, spec`: if `_sha12(rel)==spec.sha12` → OK.
2. Else if backup exists AND `_sha12(backup)==spec.sha12` → **restore** backup over `rel`, `os.utime(rel)` (White wins LWW), log `{file, was, restored: sha12, incident: True}`.
3. Else → log `{file, was, expected: sha12, action:"NEEDS-HUMAN", reason:"no-good-backup"}` (do NOT guess a restore).
4. On any `incident`, append one line to `memory/ops/revert-sentinel-log.jsonl` so the fleet sees clobber events in one place.

**Advance rule (unchanged from pin_guard, now generic):** whoever edits a watched file copies the NEW version to its backup + updates `spec.sha12` in the SAME turn. Unadvanced = next cycle reverts it (by design — that's the safety net).

## Rollout (small, reversible steps)
- [ ] Step 1: rename `pin_guard()`→`sentinel()`, move `PIN_FILES` into a module-level `REVERT_WATCH` (index.html entry preserved verbatim). Pure refactor; index.html behaviour identical.
- [ ] Step 2: add the fleet-status `agent_portal.py` entry AFTER the endpoint is re-landed + backed up (see unblock below). Do NOT add a watch entry for a file whose canonical version doesn't exist yet — that would revert live code to nothing.
- [ ] Step 3: wire `revert-sentinel-log.jsonl` into the ops status strip so clobber incidents are visible, not silent.

## Unblock step (Goal 8 fleet-status) — ONE concrete action
Re-implement `_fleet_status()` + `/api/fleet/status` in `agent_portal.py` from scratch (contract: per-host `{reachable, latency_ms, disk_pct, mem_pct, portal_up}` + overall green/amber/red; **do NOT** collide with the pre-existing `/api/health/fleet` at L4078 or the VRAM-gauge `budget_gb/used_gb` contract in core.js). Copy landed file to `memory/mechanic/agent_portal.fleet-status.bak.py`, then add it to `REVERT_WATCH`. Until then Goal 8's `(verified:)` marker is a **stale overclaim** — dashboard count of 10/10 for Mechanic is optimistic by one.

## Runbook (one-liner)
What broke: mirror LWW silently reverts any non-pinned `.py`/`.js` edit whose mtime/skew loses; only `index.html` had a sentinel. What fixes it: generalise `pin_guard()` into a `REVERT_WATCH` registry (`sentinel()`) so every protected file restores from its named backup on sha-mismatch, logging each clobber to `revert-sentinel-log.jsonl`; advance the entry in the same turn as any edit.
