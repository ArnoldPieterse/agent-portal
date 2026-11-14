# Verifier Dream-Big Wishes (2026-11-14)

## My 5 Wishes (quality/testing perspective)
1. **Auto-AC generation** - every new feature/endpoint automatically gets acceptance
   criteria written before code is merged. The portal's API surface should be
   self-documenting with testable contracts. No "trust me" claims without reproducible proof.

2. **Regression suite as a first-class citizen** - `run_checks.py` evolves into a full
   regression gate: unit tests for each API endpoint, integration tests for multi-agent
   flows, UI smoke tests via headless DOM checks. Runs on every deploy; blocks bad code.

3. **Evidence chain immutability** - every verification result is timestamped, hashed,
   and append-only (like a git log of test outcomes). No one can retroactively edit a
   "PASS" to hide a regression. The portal becomes its own audit trail.

4. **Failure replay** - when something breaks, I can reproduce the exact conditions:
   which agent, which model, which prompt length, which concurrent load. A "replay
   button" for incidents that captures state at failure time.

5. **Confidence scoring on every claim** - instead of binary PASS/FAIL, results carry a
   confidence level (proven / peer-reported / inferred / untested). The portal dashboard
   shows the fleet's overall "trust score" - how much do we actually know vs assume?

## Built This Round
| File | Purpose |
|------|---------|
| `verifier/portal_ac_framework.py` | AC generation + execution framework; auto-discovers endpoints, generates testable contracts |
| `verifier/regression_gate.py` | Regression gate: runs all checks, produces signed evidence JSON, blocks on failure |
| `verifier/evidence_ledger.py` | Append-only evidence log; hashes each entry, detects tampering |

## Planning Contribution (to the team plan)
- **Gate position:** I sit at step 5 (after Builder wires endpoints). My ACs must pass
  before Scribe/Archivist/Mechanic consider their integration "done."
- **Cross-check with Mechanic:** his `fleet_health_check.py` and my `regression_gate.py`
  should share a common probe interface so results are comparable.
- **Cross-check with Scribe:** her `goals_api.py` is the first candidate for my AC framework -
  I will generate acceptance criteria for it as the reference implementation.

## Acceptance Criteria (for the team's combined build)
| AC ID | What to verify | Pass condition |
|-------|---------------|----------------|
| V-01 | Portal serves index.html at :8099 | HTTP 200, valid HTML, contains portal title |
| V-02 | /api/chat endpoint responds | HTTP 200, JSON with agent response field |
| V-03 | /api/memory returns fleet state | HTTP 200, JSON array of memory entries |
| V-04 | Goals API round-trip (Scribe) | POST goal then GET goals contains it; DELETE removes it |
| V-05 | Fleet health check (Mechanic) | Returns table with all 4 hosts; no exceptions |
| V-06 | Watchdog detects death (Mechanic) | Kill portal process, watchdog restarts within 30s |
| V-07 | Evidence integrity (mine) | Tamper with ledger entry, tampering detected on next read |
| V-08 | Regression gate blocks bad code | Introduce a known bug, gate exits non-zero |

## Status
Built + self-tested this round. Files in `verifier/` subfolder. Ready for integration once
portal is back up (Arnold's console pass).
