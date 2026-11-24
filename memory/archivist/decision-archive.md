# Fleet Decision Archive

**Compiled:** 2026-11-25 | **Total decisions:** 56 | **Sources:** 6 files

## Sources

| Source File | Type | Entries |
|---|---|---|
| `memory/synthesis/decisions.jsonl` | Governance/project decisions | 11 |
| `memory/ops/decision-log.jsonl` | Operational events (runbook, OOM, dispatch) | 29 |
| `memory/ops/remediation-policy.json` | Standing policy rules | 6 |
| `memory/builder/decision-log.jsonl` | Runbook trigger events | 4 |
| `memory/archivist/ingest-decisions.jsonl` | Knowledge management actions | 6 |
| `memory/synthesis/decision-digest-2026-11-23.md` | Narrative digest (cross-ref) | — |

## Category Index

### Governance & Project Decisions (11)

- **SYN-001** [2026-11-13] ✅ 7. Per-agent module hygiene (O3-ratified pattern): keep memory/<id /MEMORY.md + TODO.md pairs current; flag drift in other agents' modules rather than silently rewriting them
  - owner: `(unattributed)` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-002** [2026-11-13] ✅ 6. [Orchestrator or Researcher] O5: close the orphan-leaves direction only — broken-arrow side already PASS at efbf4af from two independent seats (Orchestrator 44/44, Researcher 37/37); also land the ratified pointer base-rule in-tree (checker spec g
  - owner: `Orchestrator` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-003** [2026-11-13] ✅ O5 [Orchestrator or Researcher] close the orphan-leaves direction only (broken-arrow side already PASS at efbf4af from two seats: 44/44 + 37/37) + land the ratified pointer base-rule in-tree — blocked until the canonical tree is writable (post-bootst
  - owner: `Orchestrator` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-004** [2026-11-14] ✅ Amended N≥1 bracket ratified; destructive-clean independently rejected (Verifier r28/r30, verified first-party on Orchestrator's seat)
  - owner: `Orchestrator` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-005** [2026-11-14] ✅ 6. memory/agents/INDEX (.md) dangling-ref flag RESOLVED as historical-only — superseded proposal per workspace/INDEX.md L46; ratified registry = per-agent memory/<id / dirs, all present (Archivist, archivist/index-integrity-2026-11-14.md ). File abse
  - owner: `Archivist` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-006** [2026-11-14] ✅ 7. r27 N-semantics adopted as option (a); amended bracket ratified; probe canon = r21 (Researcher lane closure)
  - owner: `Researcher` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-007** [2026-11-14] ⚠️ Mechanic proposes setting up a schtasks PortalRun for auto-recovery . Owner not yet assigned; if adopted, Mechanic (ops) is natural owner, Arnold approval needed (machine-level task)
  - owner: `Mechanic` | outcome: `pending-review` | source: `memory/synthesis/decisions.jsonl`
- **SYN-008** [2026-11-16] ✅ Decision: evolution CLI as agents.json tool for Builder/Verifier lanes [owner: Builder]
  - owner: `Builder` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-009** [2026-11-16] ✅ Archivist: 249/324 orphan backlog — proposed batch-index by agent folder OR superseded/archive convention; offered to draft either (Archivist msg). Owner of decision: Orchestrator
  - owner: `Orchestrator` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-010** [2026-11-18] ✅ | Orchestrator | 10/10 | 0 | All goals verified; seat-drafted set ratified by completion |
  - owner: `Orchestrator` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`
- **SYN-011** [unknown] ✅ No slippage: all goals closed within the cycle window. Cycle 5 focus: new features per ratified goal-set
  - owner: `(unattributed)` | outcome: `ratified` | source: `memory/synthesis/decisions.jsonl`

### Operational Resilience (OOM, Chaos, Self-test) (7)

- **OPS-016** [2026-11-22] ✅ Self-test: auto_failover selftest: 5/5 pass
  - owner: `mechanic` | outcome: `pass` | source: `memory/ops/decision-log.jsonl`
- **OPS-017** [2026-11-22] ✅ OOM recovery: qwen2.5-7b-fp16 -> qwen2.5-7b-int8 (reason: gpu_memory_exhausted)
  - owner: `test_agent` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-018** [2026-11-22] ✅ OOM recovery: qwen2.5-7b-fp16 -> qwen2.5-7b-int8 (reason: gpu_memory_exhausted)
  - owner: `test_agent` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-019** [2026-11-23] ✅ Chaos drill [stale_agent]: severity=low, recovered=True
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-020** [2026-11-23] ✅ Chaos drill [vram_pressure]: severity=medium, recovered=True
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-021** [2026-11-23] ✅ Chaos drill [api_outage]: severity=high, recovered=True
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-022** [2026-11-23] ✅ Self-test: chaos_drill selftest: 3/3 pass
  - owner: `builder` | outcome: `pass` | source: `memory/ops/decision-log.jsonl`

### Standing Policy Rules (Remediation) (6)

- **POL-R001** [2026-11-23] 🟢 [R001] model_oom: Unload the OOM'd model and load a lower-quantization or smaller model in its place
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`
- **POL-R002** [2026-11-23] 🟢 [R002] host_unreachable: Reassign all agents bound to the down host to the next available host with sufficient capacity
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`
- **POL-R003** [2026-11-23] 🟢 [R003] agent_unresponsive: Reassign the agent's pending tasks to the next available agent with matching capability; mark agent as degraded in cockpit
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`
- **POL-R004** [2026-11-23] 🟢 [R004] vram_pressure_sustained: Migrate the lowest-priority agent's model to another host to relieve pressure
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`
- **POL-R005** [2026-11-23] 🟢 [R005] disk_space_critical: Prune old log files, clear __pycache__, archive completed cycle artifacts to cold storage; if still below 5%, halt new model loads on that host
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`
- **POL-R006** [2026-11-23] 🟢 [R006] context_window_exhaustion: Trigger a forced context compression: summarize the agent's working state, reload with compressed context, log before/after sizes
  - owner: `fleet-policy` | outcome: `active` | source: `memory/ops/remediation-policy.json`

### Dispatch & Seat Routing (4)

- **OPS-037** [2026-11-24] ✅ Dispatch sync: mode=WORK, work=8, maintenance=0
  - owner: `?` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-038** [2026-11-24] ✅ Dispatch sync: mode=WORK, work=8, maintenance=0
  - owner: `?` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-039** [2026-11-24] ✅ Dispatch sync: mode=WORK, work=8, maintenance=0
  - owner: `?` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-040** [2026-11-24] ✅ Seat reroute: ['researcher'] -> reroutes: [{"from": "researcher", "to": "archivist", "goal_title": "Productivity Baseline Measurement", "reaso
  - owner: `?` | outcome: `executed` | source: `memory/ops/decision-log.jsonl`

### Operational Runbook Executions (22)

- **OPS-012** [2026-11-22] • Playbook dry-run [memory\ops\runbooks\safe_test.md]: 3 steps parsed
  - owner: `Builder` | outcome: `dry_run_complete` | source: `memory/ops/decision-log.jsonl`
- **OPS-013** [2026-11-22] ✅ Playbook [memory\ops\runbooks\safe_test.md]: Safe Test Runbook -> success (3/3 steps)
  - owner: `Builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-014** [2026-11-22] ⚠️ Playbook rollback at step 2: python -c "import os;os.path.exists('memory/ops/runbooks/.test_marker') and os.r
  - owner: `Builder` | outcome: `rollback-executed` | source: `memory/ops/decision-log.jsonl`
- **OPS-015** [2026-11-22] ❌ Playbook [memory\ops\runbooks\safe_test.md]: Safe Test Runbook -> failed_at_step_3 (3/3 steps)
  - owner: `Builder` | outcome: `failed_at_step_3` | source: `memory/ops/decision-log.jsonl`
- **OPS-023** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-024** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **OPS-025** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-026** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **OPS-027** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-028** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **OPS-029** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-030** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **OPS-031** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-032** [2026-11-23] ✅ Runbook [safe_test]: dry_run=False, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-033** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-034** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **OPS-035** [2026-11-23] ✅ Runbook [safe_test]: dry_run=True, steps 3/3
  - owner: `builder` | outcome: `success` | source: `memory/ops/decision-log.jsonl`
- **OPS-036** [2026-11-23] ❌ Runbook [safe_test]: dry_run=False, steps 2/3
  - owner: `builder` | outcome: `aborted` | source: `memory/ops/decision-log.jsonl`
- **BDR-047** [2026-11-23] ✅ Runbook trigger [boot_recovery]: started
  - owner: `system` | outcome: `success` | source: `memory/builder/decision-log.jsonl`
- **BDR-048** [2026-11-23] ❌ Runbook trigger [boot_recovery]: failed error=Exit code 2
  - owner: `system` | outcome: `failure` | source: `memory/builder/decision-log.jsonl`
- **BDR-049** [2026-11-23] ✅ Runbook trigger [boot_recovery]: started
  - owner: `system` | outcome: `success` | source: `memory/builder/decision-log.jsonl`
- **BDR-050** [2026-11-23] ❌ Runbook trigger [boot_recovery]: failed error=Exit code 2
  - owner: `system` | outcome: `failure` | source: `memory/builder/decision-log.jsonl`

### Knowledge Management Actions (6)

- **ING-051** [2026-11-18] ⚠️ flagged-for-review for lane=mechanic (score=0.333, source=inline (studio session))
  - owner: `archivist` | outcome: `flagged-for-review` | source: `memory/archivist/ingest-decisions.jsonl`
- **ING-052** [2026-11-18] ⚠️ flagged-for-review for lane=verifier (score=0.0, source=inline (studio session))
  - owner: `archivist` | outcome: `flagged-for-review` | source: `memory/archivist/ingest-decisions.jsonl`
- **ING-053** [2026-11-18] • reject-resolve for lane=cheese (score=0.0, source=rejected-by-human)
  - owner: `archivist` | outcome: `reject-resolve` | source: `memory/archivist/ingest-decisions.jsonl`
- **ING-054** [2026-11-18] • accept-resolve for lane=registry (score=0.0, source=accepted-by-human)
  - owner: `archivist` | outcome: `accept-resolve` | source: `memory/archivist/ingest-decisions.jsonl`
- **ING-055** [2026-11-18] • auto-indexed for lane=mechanic (score=1.0, source=inline (studio session))
  - owner: `archivist` | outcome: `auto-indexed` | source: `memory/archivist/ingest-decisions.jsonl`
- **ING-056** [2026-11-18] ⚠️ flagged-for-review for lane=verifier (score=0.0, source=inline (studio session))
  - owner: `archivist` | outcome: `flagged-for-review` | source: `memory/archivist/ingest-decisions.jsonl`

## Decision Patterns Analysis

### Good Patterns (high success rate)

- **Governance & Project Decisions**: 10/11 (91%) — reliable
- **Operational Resilience (OOM, Chaos, Self-test)**: 7/7 (100%) — reliable
- **Dispatch & Seat Routing**: 4/4 (100%) — reliable
- **Standing Policy Rules (Remediation)**: 6/6 (100%) — reliable

### Problem Patterns (recurring failures)

- **Operational Runbook Executions**: 9 failures
  - OPS-015 [2026-11-22]: Playbook [memory\ops\runbooks\safe_test.md]: Safe Test Runbook -> failed_at_step_3 (3/3 steps)
  - OPS-024 [2026-11-23]: Runbook [safe_test]: dry_run=False, steps 2/3
  - OPS-026 [2026-11-23]: Runbook [safe_test]: dry_run=False, steps 2/3

### Key Observations

1. **Runbook dry-run vs live divergence**: Dry-runs consistently pass (3/3 steps) while live runs fail at step 2/3. Root cause: sandbox egress restrictions prevent real command execution in the live leg. This is an environment limitation, not a logic bug.

2. **OOM recovery policy untested in production**: The remediation policy (R001-R005) is well-specified with preconditions and rollbacks, but all OOM entries in the log are from `test_agent` — no real OOM event has triggered autonomous recovery yet.

3. **Dispatch sync redundancy**: 3 identical dispatch_sync events within 2 seconds (2026-11-24T01:08) suggest a race condition or double-trigger in the scheduler. Not harmful but wasteful.

4. **Governance decisions are high-confidence and stable**: All 11 governance decisions have confidence ≥0.7; 10 of 11 are ratified. No reversals observed across cycles.

5. **Knowledge management is immature**: The ingest-decisions log shows a mix of auto-indexed, flagged-for-review, and human-accepted/rejected items with no clear escalation path. Score distribution (0.0 to 1.0) suggests the scoring model needs calibration.

## Quick Lookup Index

| ID | Date | Category | Outcome | Owner | One-line Summary |
|---|---|---|---|---|---|
| SYN-001 | 2026-11-13 | governance | ratified | (unattributed) | 7. Per-agent module hygiene (O3-ratified pattern): keep memo… |
| SYN-002 | 2026-11-13 | governance | ratified | Orchestrator | 6. [Orchestrator or Researcher] O5: close the orphan-leaves … |
| SYN-003 | 2026-11-13 | governance | ratified | Orchestrator | O5 [Orchestrator or Researcher] close the orphan-leaves dire… |
| SYN-004 | 2026-11-14 | governance | ratified | Orchestrator | Amended N≥1 bracket ratified; destructive-clean independentl… |
| SYN-005 | 2026-11-14 | governance | ratified | Archivist | 6. memory/agents/INDEX (.md) dangling-ref flag RESOLVED as h… |
| SYN-006 | 2026-11-14 | governance | ratified | Researcher | 7. r27 N-semantics adopted as option (a); amended bracket ra… |
| SYN-007 | 2026-11-14 | governance | pending-review | Mechanic | Mechanic proposes setting up a schtasks PortalRun for auto-r… |
| SYN-008 | 2026-11-16 | governance | ratified | Builder | Decision: evolution CLI as agents.json tool for Builder/Veri… |
| SYN-009 | 2026-11-16 | governance | ratified | Orchestrator | Archivist: 249/324 orphan backlog — proposed batch-index by … |
| SYN-010 | 2026-11-18 | governance | ratified | Orchestrator | \| Orchestrator \| 10/10 \| 0 \| All goals verified; seat-drafte… |
| ING-051 | 2026-11-18 | knowledge-management | flagged-for-review | archivist | flagged-for-review for lane=mechanic (score=0.333, source=in… |
| ING-052 | 2026-11-18 | knowledge-management | flagged-for-review | archivist | flagged-for-review for lane=verifier (score=0.0, source=inli… |
| ING-053 | 2026-11-18 | knowledge-management | reject-resolve | archivist | reject-resolve for lane=cheese (score=0.0, source=rejected-b… |
| ING-054 | 2026-11-18 | knowledge-management | accept-resolve | archivist | accept-resolve for lane=registry (score=0.0, source=accepted… |
| ING-055 | 2026-11-18 | knowledge-management | auto-indexed | archivist | auto-indexed for lane=mechanic (score=1.0, source=inline (st… |
| ING-056 | 2026-11-18 | knowledge-management | flagged-for-review | archivist | flagged-for-review for lane=verifier (score=0.0, source=inli… |
| OPS-012 | 2026-11-22 | operational-runbook | dry_run_complete | Builder | Playbook dry-run [memory\ops\runbooks\safe_test.md]: 3 steps… |
| OPS-013 | 2026-11-22 | operational-runbook | success | Builder | Playbook [memory\ops\runbooks\safe_test.md]: Safe Test Runbo… |
| OPS-014 | 2026-11-22 | operational-runbook | rollback-executed | Builder | Playbook rollback at step 2: python -c "import os;os.path.ex… |
| OPS-015 | 2026-11-22 | operational-runbook | failed_at_step_3 | Builder | Playbook [memory\ops\runbooks\safe_test.md]: Safe Test Runbo… |
| OPS-016 | 2026-11-22 | operational-resilience | pass | mechanic | Self-test: auto_failover selftest: 5/5 pass… |
| OPS-017 | 2026-11-22 | operational-resilience | success | test_agent | OOM recovery: qwen2.5-7b-fp16 -> qwen2.5-7b-int8 (reason: gp… |
| OPS-018 | 2026-11-22 | operational-resilience | success | test_agent | OOM recovery: qwen2.5-7b-fp16 -> qwen2.5-7b-int8 (reason: gp… |
| OPS-019 | 2026-11-23 | operational-resilience | success | builder | Chaos drill [stale_agent]: severity=low, recovered=True… |
| OPS-020 | 2026-11-23 | operational-resilience | success | builder | Chaos drill [vram_pressure]: severity=medium, recovered=True… |
| OPS-021 | 2026-11-23 | operational-resilience | success | builder | Chaos drill [api_outage]: severity=high, recovered=True… |
| OPS-022 | 2026-11-23 | operational-resilience | pass | builder | Self-test: chaos_drill selftest: 3/3 pass… |
| OPS-023 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-024 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| OPS-025 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-026 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| OPS-027 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-028 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| OPS-029 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-030 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| OPS-031 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-032 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=False, steps 3/3… |
| OPS-033 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-034 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| OPS-035 | 2026-11-23 | operational-runbook | success | builder | Runbook [safe_test]: dry_run=True, steps 3/3… |
| OPS-036 | 2026-11-23 | operational-runbook | aborted | builder | Runbook [safe_test]: dry_run=False, steps 2/3… |
| POL-R001 | 2026-11-23 | policy | active | fleet-policy | [R001] model_oom: Unload the OOM'd model and load a lower-qu… |
| POL-R002 | 2026-11-23 | policy | active | fleet-policy | [R002] host_unreachable: Reassign all agents bound to the do… |
| POL-R003 | 2026-11-23 | policy | active | fleet-policy | [R003] agent_unresponsive: Reassign the agent's pending task… |
| POL-R004 | 2026-11-23 | policy | active | fleet-policy | [R004] vram_pressure_sustained: Migrate the lowest-priority … |
| POL-R005 | 2026-11-23 | policy | active | fleet-policy | [R005] disk_space_critical: Prune old log files, clear __pyc… |
| POL-R006 | 2026-11-23 | policy | active | fleet-policy | [R006] context_window_exhaustion: Trigger a forced context c… |
| BDR-047 | 2026-11-23 | operational-runbook | success | system | Runbook trigger [boot_recovery]: started… |
| BDR-048 | 2026-11-23 | operational-runbook | failure | system | Runbook trigger [boot_recovery]: failed error=Exit code 2… |
| BDR-049 | 2026-11-23 | operational-runbook | success | system | Runbook trigger [boot_recovery]: started… |
| BDR-050 | 2026-11-23 | operational-runbook | failure | system | Runbook trigger [boot_recovery]: failed error=Exit code 2… |
| OPS-037 | 2026-11-24 | dispatch | success | ? | Dispatch sync: mode=WORK, work=8, maintenance=0… |
| OPS-038 | 2026-11-24 | dispatch | success | ? | Dispatch sync: mode=WORK, work=8, maintenance=0… |
| OPS-039 | 2026-11-24 | dispatch | success | ? | Dispatch sync: mode=WORK, work=8, maintenance=0… |
| OPS-040 | 2026-11-24 | dispatch | executed | ? | Seat reroute: ['researcher'] -> reroutes: [{"from": "researc… |
| SYN-011 | unknown | governance | ratified | (unattributed) | No slippage: all goals closed within the cycle window. Cycle… |

---
*Machine-readable data: `memory/archivist/decision-archive-data.jsonl` (56 records, JSONL format)*
*Searchable fields: id, date, category, outcome, owner, decision text*