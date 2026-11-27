# Steady-State Decision-Logic Self-Test (sandbox-gateable) - 2026-11-25T15:32Z

## Why (round topic: Fleet Autonomy Convergence)
The cockpit convergence state machine (`_applyFleetState` in ui/uploads.js L514-527)
was verified only statically + 6/7 spec checks; the last leg ("no console errors")
and the @375 screenshot leg were blocked on a non-sandbox browser seat (no node /
playwright in this host). This pass converts the PURE-LOGIC leg into a
sandbox-runnable self-test so Forge can gate the convergence state machine WITHOUT
a browser seat - removing one human/non-sandbox bottleneck.

## What
memory/pixel/steady_state_selftest.py - faithful Python port of the exact
`_applyFleetState` expressions (c1 = fleet_pct>=100; c2 = every agent open==0,
vacuously true on empty list; steady/converging/active + partial-bar text).

## Verification (ran in this sandbox)
- 11/11 PASS, exit 0.
- Covers: guard no-op (None / ok=false), steady (100%+all closed), boundary pct==100.0,
  converging c2-only (99.9%, 87%), converging c1-only (100% w/ open agent -> "steady-state pending"),
  active (neither), empty-agents vacuous-true, missing fields, null-open-as-closed.

## Scope honesty
Verifies DECISION LOGIC only. Does NOT cover DOM render or Playwright console-error
checks - those still need a live browser seat (unchanged, already logged).

## Gate hook for Forge
`python memory/pixel/steady_state_selftest.py` -> exit 0 = convergence state machine logic green.
