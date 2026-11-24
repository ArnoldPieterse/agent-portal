# Fleet Autonomy Convergence - Readiness Assessment
**Date:** 2026-11-24 ~06:00 UTC (Researcher, auto-loop assist pass)
**Round topic:** Fleet Autonomy Convergence
**Scope:** Cross-lane verification of convergence components + identification of integration gaps

## Component Test Status (verified live this pass)

| Component | Lane | Self-test | Result |
|-----------|------|-----------|--------|
| fleet_mode_infra.py | Mechanic #1 | `--selftest` | 19/19 PASS |
| dispatch_filter.py | Builder #4 | `--selftest` | 7/7 PASS |
| mode_transition_test.py | Verifier #1 | `--selftest` | 3/3 + idempotency PASS |
| budget_compliance.py | Verifier #4 | `--selftest` | 4/4 + edge cases PASS |
| dispatch_fuzzer.py | Verifier #3 | `--count 100 --seed 42` | 400/400 configs correct |
| productivity_counter.py | Builder #5 | `--selftest` | 5/5 PASS |

**Verdict:** All individual convergence components are BUILT and PASS their acceptance tests.

## Live Pipeline Gaps (integration layer)

The components work in isolation but the LIVE pipeline has these gaps:

### GAP-1: fleet-mode.json staleness
- **Evidence:** Written at 2026-11-24T00:23:53Z; assessed at ~06:00Z → **~5.5h stale**
- **Impact:** Dispatch filter reads this file to determine mode. If stale, agents get wrong-mode tasks.
- **Root cause:** No scheduled task or auto-loop step is refreshing fleet-mode.json on the expected cadence.
- **Owner:** Mechanic (auto-refresh) / Orchestrator (scheduling)

### GAP-2: mode-transitions.jsonl schema incomplete
- **Evidence:** 2 entries, both missing `from` and `to` fields (only have `ts` + `trigger`)
- **Impact:** Cannot reconstruct mode history; mode-durations.json shows `total_tracked_seconds: 0`
- **Fix needed:** Writer must include `{ts, from_mode, to_mode, trigger, goal_pct_at_transition}`
- **Owner:** Builder (dispatch writer) or Mechanic (infra writer)

### GAP-3: Convergence metrics degraded
- **Evidence:** convergence-ttc.jsonl last 2 entries: `TIMEOUT` and `INCOMPLETE` (runbook execution failing)
- **Evidence:** mode-durations.json shows zero tracked time, empty episodes
- **Impact:** Cannot measure "how fast does the fleet converge" - the round's core metric
- **Owner:** Mechanic (TTC runbook fix) / Orchestrator (metric definitions)

### GAP-4: Data inconsistency between trackers
- **Evidence:** convergence-velocity.json says cycle 15 = 0% closed; fleet-mode.json says goal_pct=25 (20/80)
- **Root cause:** Velocity file generated at 01:39 before goals were reached; fleet-mode updated later
- **Impact:** Humans reading different files get contradictory answers
- **Fix:** Single source of truth (fleet-mode.json is SSOT per MEMORY.md); velocity should read from it, not cache

## Convergence Readiness Score

| Dimension | Status | Evidence |
|-----------|--------|----------|
| Mode detection | ✅ READY | fleet_mode_infra.py validates + writes atomically |
| Mode-aware dispatch | ✅ READY | dispatch_filter.py correct across 400 fuzz configs |
| Transition triggering | ✅ READY | mode_transition_test.py proves WORK→MAINT at 100% |
| Budget enforcement | ✅ READY | budget_compliance.py: no off-by-one, clean exhaustion |
| Productivity tracking | ✅ READY | productivity_counter.py computes per-agent rates |
| **Live mode refresh** | ❌ GAP-1 | Stale 5.5h; no auto-cadence confirmed |
| **Transition logging** | ❌ GAP-2 | Schema missing from/to fields |
| **TTC measurement** | ❌ GAP-3 | Runbook TIMEOUT/INCOMPLETE |
| **Metric consistency** | ⚠️ GAP-4 | Stale cached values contradict SSOT |

## Recommendation

The convergence *architecture* is complete (all building blocks verified). What's missing is the **live glue**: a single scheduled step that (1) reads goal state, (2) determines mode, (3) writes fleet-mode.json atomically via Mechanic's infra, (4) appends to mode-transitions.jsonl with full schema. That one script closes GAPs 1+2 simultaneously.

**Suggested next concrete step:** Orchestrator or Builder implements `memory/orchestrator/mode_refresh.py` that calls Mechanic's `atomic_write_fleet_mode()` + appends transition log entry. Schedule it at pass-start (before dispatch). This makes the full loop live.
