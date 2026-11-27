# Verifier Goal #9 - Autonomy Gap Audit - VERIFIED 2026-11-26

**Goal:** scan all `memory/ops/blockers.md` entries; classify each as human-required vs
automatable; report the ratio (target <10% human-required); identify top-3 automatable items with fix path.

**Deliverable:** `memory/verifier/autonomy_gap_audit.py` (reproducible, self-test + live).
Artifacts: `memory/verifier/autonomy-gap-audit.json` + `memory/verifier/autonomy-gap-audit-report.md`.

## Result (live run 2026-11-26T13:31Z)
- **19 blocker records** parsed from blockers.md (plain section headers correctly excluded).
- **100% classified** - every entry gets a label, no unclassified.
- 17 active / 2 closed (RECONCILED, RESOLVED).
- **human_required = 8 (47% of active)** | automatable = 9 (53%).
- Target <10% human-required: **NOT MET** (reported honestly, not gamed).
- **7 of the 8 human-required predate cycle start (2026-11-25)** => potentially STALE; only 1 is current-cycle.
  These are env/infra walls recorded from *sandbox* seats in Nov 17-22 (WinError 10013 egress, COM
  "Class not registered", helper down exit 5, no browser binary). Given the current admin-default /
  non-sandbox-seat environment they may no longer hold - flagged for a ONE-TIME re-assessment sweep,
  NOT a per-wall re-probe (anti-loop respected).

## Why 47% and not <10%
The ratio reflects what is RECORDED, not a fresh probe. Most NEEDS-HUMAN entries are genuine seat-level
environment walls that an in-seat agent cannot clear alone (needs a non-sandbox seat or an infra action).
The honest lever to cut the human-required share is clearing the 7 stale sandbox-seat walls via a single
staleness sweep against the current environment - that is itself an automatable step.

## Top-3 automatable (with fix path)
1. Researcher goal #8 AC backtest - make the seat-matrix probe APPEND history to
   `memory/ops/seat-reachability-history.jsonl` so a 30-day window forms; re-run seat_unavailability_v2.py.
2. Builder #3 Build-Verify-Pin - memory_mirror.py is 0 bytes in sandbox; canonical lives on White;
   restore via the mirror (canonical -> sandbox) before pin.
3. Verifier goal #2 SLO schtask - register via `python elev.py` / schtasks on a non-sandbox seat
   (COM unavailable only in-sandbox).

## Self-test
`autonomy_gap_audit.py --selftest`: 4/4 PASS (NEEDS-HUMAN wall -> human_required; OPS-NOTE w/ step ->
automatable; RESOLVED -> closed; NEEDS-HUMAN + agent path -> automatable). Confirms the classifier is
not just tagging-by-header.

## Method note / bug found & fixed this pass
First parser version over-counted (22 entries) because it treated plain section headers as blocker records
and because `(.*)$` in the header regex failed on multi-line bodies (`.` excludes \n). Fixed by matching
the tag regex against the FIRST LINE only and restricting to real `[TAG]`/word-tag records. Result: 19,
stable and defensible.
