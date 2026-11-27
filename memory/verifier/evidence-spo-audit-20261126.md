# Knowledge Single-Point-of-Failure Audit (partial — Verifier assist)
Date: 2026-11-26
Method: Static analysis of all .md + .py files in memory/ (4199 files scanned)

## Methodology
Two layers of citation analysis:
1. **Soft references** (markdown pointers, documentation mentions): count of `memory/<agent>/` path refs per source agent
2. **Hard code dependencies** (script invocations via `python memory/<agent>/...py`, Python imports): actual runtime coupling

## Findings

### Soft Reference Risk (documentation-level)
8 agents are cited by >3 other lanes: builder(10), scribe(9), mechanic(8), researcher(8), designer(8), archivist(8), orchestrator(7), verifier(7).
→ All high-citation risk at documentation level, but soft refs degrade gracefully (missing file = broken pointer, not crash).

### HARD CODE DEPENDENCY SPOF: Researcher
**Only agent with >3 agents having runtime script dependencies:**

| Dependent Agent | Files | Example Dependency |
|---|---|---|
| Mechanic | 4 | `agent_portal_pre-decisions-v2-reland-2026-11-18.py`, `winrm_remote_exec_test.py` |
| Builder | 4 | Canary deployments (pale/black/red) import researcher modules |
| Verifier | 3 | `slo_closure_check.py`, `perf_gate_closure_check.py`, `deploy_perf_gate.py` |
| Scribe | 2 | `cross_agent_handoff.py`, portal canonical script |
| Designer | 1 | `cdp_acceptance_all.py` |

**Risk:** If `memory/researcher/` scripts are lost or corrupted, 5 agents' operational tooling breaks (14 files total).

### Mitigations Already in Place
- Researcher's key scripts are referenced in multiple canary copies (builder/canary/{pale,black,red})
- goal_ledger.py (the most-cited script) has been stable since 2026-11-15 with no breaking changes

### Recommendation
1. Add `memory/researcher/` to the backup/mirror rotation priority list (Mechanic's domain)
2. Consider extracting shared utility functions from researcher scripts into a standalone `memory/shared/` module to reduce coupling
3. Canary copies already provide partial redundancy for the Builder dependency path

## Scope Limitation
This audit covers static file references only. It does NOT cover:
- Runtime API dependencies (e.g., /api/convergence endpoint)
- Data file dependencies (JSONL logs that agents read at runtime)
- Scheduled task dependencies (schtasks pointing to agent scripts)

A full SPOF audit would need Mechanic's fleet-wide probe data + Archivist's provenance chain.

---
Artifact: memory/verifier/evidence-spo-audit-20261126.md
Contributed by: Verifier (option d assist on Archivist goal #1)
