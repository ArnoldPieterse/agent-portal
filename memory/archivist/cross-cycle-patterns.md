# Cross-Cycle Pattern Archive
**Lane:** Archivist | **Compiled:** 2026-11-25 | **Scope:** Cycles 1-17, all agents
**Sources:** cross_patterns_report.md, completion-patterns.md, cross-patterns-cycle10.md, blocker-trends.md, decision-archive.md

---

## 1. Completion Rate Patterns

### By Goal Type (cycles 1-9, n=410)
| Type | Verified/Total | Rate | Interpretation |
|------|---------------|------|----------------|
| research | 55/58 | 95% | Bounded scope; easy to verify |
| verify | 93/105 | 89% | Binary pass/fail; clear evidence |
| build | 142/166 | 86% | Multi-step but well-defined |
| ops | 49/58 | 84% | External deps (hosts, models) |
| design | 19/23 | 83% | Subjective acceptance criteria |

### By Agent (cycles 1-9)
| Agent | Rate | Notes |
|-------|------|-------|
| orchestrator | 96% | Highest; goal-setting aligns with own capabilities |
| archivist | 92% | Knowledge work is self-contained |
| scribe | 90% | Synthesis tasks are bounded |
| verifier | 87% | Test-driven closure |
| mechanic | 86% | Ops work depends on fleet state |
| researcher | 84% | Research scope can expand |
| builder | 82% | Build complexity varies |
| designer | 82% | UI acceptance is subjective |

### By Cycle (trend)
| Cycle | Rate | Note |
|-------|------|------|
| 1 | 93% | Early; small scope |
| 4 | 85% | — |
| 5 | 78% | Scope expansion |
| 6 | 94% | Recovery |
| 7 | 100% | Perfect cycle (small n) |
| 9 | 74% | Lowest; scope creep visible |

**Trend:** Completion rate oscillates between 74-100% with no clear upward or downward trend. The variance correlates with goal count per cycle (more goals = lower rate, suggesting diminishing returns on parallel work).

---

## 2. Throughput & Capacity Patterns

### Cross-Cycle Throughput (cycles 10+, n=510)
- Overall: 316/510 verified (62%), 194 still open
- Designer is the lowest throughput agent (47%) — consistent with subjective acceptance criteria
- Orchestrator highest (76%) but has the most total goals (87)

**Emerging pattern:** Throughput parity across agents suggests the bottleneck is NOT agent capability but external dependency (model availability, host capacity). This aligns with the convergence-health FAIL status (missing seat-matrix, stale autonomy data).

---

## 3. Blocker Patterns

### Blocker Classes (frequency)
| Class | Count | Root Cause | Resolution Path |
|-------|-------|-----------|-----------------|
| sandbox egress wall | 4 | Network isolation of sandbox seats | Run from White host |
| helper down / absent | 2 | elev.py not deployed or service down | Deploy + repair on target host |
| seat-unreachable | 3 | Model not loaded on any host | Load model via LM Studio API |
| file-absent | 1 | Sandbox filesystem incomplete | Sync from canonical host |

**Key insight:** 80% of blockers are environmental (sandbox isolation, model loading) rather than logical. These cannot be resolved by the agent itself — they require either a different seat or a one-time setup action.

### Blocker Resolution Time
- Average: 48h (only 1 dated pair available — insufficient sample)
- Pattern: Most blockers persist until the next cycle when a different seat handles the task

---

## 4. Decision Patterns (from decision-archive.md)

### High-Reliability Patterns
1. **Governance decisions** (10/11 ratified, confidence ≥0.7): Stable across cycles, no reversals
2. **Policy rules R001-R005**: Well-specified with preconditions + rollback; untested in production but logically sound
3. **Chaos drills** (3/3 pass): Recovery mechanisms work as designed

### Problem Patterns
1. **Runbook dry-run vs live divergence**: Dry-runs pass 3/3, live runs fail at step 2/3. Root cause: sandbox egress prevents real command execution. NOT a logic bug — environment limitation.
2. **Dispatch sync race condition**: 3 identical events within 2s (2026-11-24T01:08). Wasteful but harmless.
3. **Knowledge management immaturity**: Ingest scoring (0.0-1.0) lacks calibration; no escalation path for flagged items.

---

## 5. Reopened Topics (Slip Indicators)

20 topics were reopened across cycles, concentrated in:
- **Orchestrator hot-load/activation** (5 topics): model lifecycle management keeps expanding scope
- **VRAM/capacity prediction** (3 topics): predictor accuracy requires more data than initially available
- **Portal UI** (4 topics): iterative refinement; each fix reveals next issue

**Pattern:** Reopened topics cluster around areas where the first-pass solution was correct in principle but incomplete in scope. The "v1 marker" pattern (goal says "done" but v2 is needed) appears in ~40% of reopened items.

---

## 6. Cross-Agent Coordination Patterns

### Topic Overlap (coordination risk)
- **semantic search index** → researcher + archivist (both building similar capability)
- **cycle retrospective automation** → orchestrator + scribe (duplicate scope)

### Theme Specialization (healthy division of labor)
- Mechanic: auto(24), log(21), alert(12), recover(9) — ops specialist
- Verifier: test(25), verify(12) — QA specialist
- Orchestrator: log(25), auto(21) — coordination + automation
- Researcher: recover(6), test(6) — investigation + validation

### Assist Patterns (cross-lane help)
- Mechanic assists Scribe (decision v2 reland, 2026-11-18)
- Orchestrator assists Builder (convergence endpoint, 2026-11-25)
- Archivist assists Verifier (evidence for decision index, 2026-11-24)

**Pattern:** Assist flows follow capability matching — ops agents help with infrastructure, knowledge agents help with documentation. No circular dependencies observed.

---

## 7. Emerging Trends (cycles 15-17, convergence phase)

1. **Convergence metrics are being formalized**: SSOT document, metric lineage, provenance chains all landed in cycle 17. This creates the audit trail needed for steady-state entry.
2. **Decision quality tracking is nascent**: decision-quality.json shows "insufficient_data" — the infrastructure exists but hasn't accumulated enough production decisions to generate a trend.
3. **Steady-state readiness is at 60%**: All three entry criteria unmet (E1: 60%, E2: 69.1, E3: max 2/agent). The gap is primarily in pass_autonomy (58.3) — reducing human interventions is the highest-leverage action.
4. **Cycle duration is stable at ~24h**: No anomaly risk (X3 exit criterion not triggered).

---

## Deduplication Log

| Duplicate Found | Kept | Removed/Noted |
|----------------|------|---------------|
| cross_patterns_report.md vs cross-patterns-cycle10.md | cycle10 (more recent, same data) | goals/cross_patterns_report.md is earlier snapshot |
| completion-patterns.md vs completion-patterns-2026-11-23.md | main file (full analysis) | -2026-11-23 is a 742B summary stub |
| blocker-trends.md vs ops/blockers.md | both kept (different scopes: trends vs raw log) | — |

---

*Machine-readable source data: `memory/goals/cross_patterns_report.md`, `memory/synthesis/completion-patterns.md`, `memory/synthesis/blocker-trends.md`*
