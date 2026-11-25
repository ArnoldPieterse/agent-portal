# Agent Autonomy Contribution Matrix
**Generated:** 2026-11-25 14:26 | **Scribe goal #7**
**Sources:** decision-autonomy-map.jsonl, intervention-patterns.jsonl, lane artifacts

## Summary Table

| Rank | Agent | Automations Built | Interventions Eliminated | Interventions Still Received | Score Contribution |
|------|-------|------------------|--------------------------|------------------------------|-------------------|
| 1 | Researcher | 3 | 3 | 1 | 9.1 |
| 2 | Mechanic | 3 | 3 | 0 | 8.9 |
| 3 | Orchestrator | 3 | 3 | 1 | 8.2 |
| 4 | Builder | 2 | 2 | 1 | 7.4 |
| 5 | Verifier | 2 | 2 | 0 | 6.8 |
| 6 | Archivist | 2 | 2 | 0 | 6.2 |
| 7 | Scribe | 3 | 3 | 0 | 5.7 |
| 8 | Designer | 1 | 1 | 1 | 3.8 |
| 9 | Outlet | 1 | 1 | 2 | 3.1 |
| 10 | Pixel | 1 | 1 | 1 | 2.8 |

**Total score (sum of contributions):** 62.0
**Composite autonomy score (cycle 23):** 71.3

## Top-3 Contributors

**#1 Researcher** (9.1): 3 automations (goal_ledger.py, kb_index.py, evidence_quality_trend.py)
**#2 Mechanic** (8.9): 3 automations (boot_recovery.py, portal_watchdog.py, model_lifecycle.py)
**#3 Orchestrator** (8.2): 3 automations (goal_prioritizer.py, cycle_estimator.py, convergence_api.py)

## Per-Agent Detail

### Researcher (Rank 1, Contribution 9.1)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/researcher/goal_ledger.py` | manual goal tracking |
| `memory/researcher/kb_index.py` | manual knowledge retrieval |
| `memory/researcher/evidence_quality_trend.py` | manual evidence QA |

### Mechanic (Rank 2, Contribution 8.9)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/ops/boot_recovery.py` | portal-down manual restart |
| `memory/mechanic/portal_watchdog.py` | portal health monitoring |
| `memory/ops/model_lifecycle.py` | manual model load/unload |

### Orchestrator (Rank 3, Contribution 8.2)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/orchestrator/goal_prioritizer.py` | manual goal ranking |
| `memory/orchestrator/cycle_estimator.py` | manual cycle duration estimation |
| `memory/orchestrator/convergence_api.py` | manual convergence status check |

### Builder (Rank 4, Contribution 7.4)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/builder/evolution_fitness_test.py` | manual evolution validation |
| `memory/builder/frontend-build/` | manual UI assembly |

### Verifier (Rank 5, Contribution 6.8)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/verifier/evolution_gate.py` | manual regression check |
| `memory/verifier/test_battery.py` | manual test execution |

### Archivist (Rank 6, Contribution 6.2)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/archivist/index_check.py` | manual pointer-map audit |
| `memory/archivist/provenance_report.py` | manual source verification |

### Scribe (Rank 7, Contribution 5.7)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/scribe/autonomy_trend.py` | manual score tracking |
| `memory/scribe/intervention_classifier.py` | manual intervention categorization |
| `memory/scribe/milestones_tracker.py` | manual milestone tracking |

### Designer (Rank 8, Contribution 3.8)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/designer/cockpit-panel-spec.md` | manual UI spec writing |

### Outlet (Rank 9, Contribution 3.1)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/outlet/profile-registry.md` | manual voice consistency check |

### Pixel (Rank 10, Contribution 2.8)

| File | Intervention Class Eliminated |
|------|------------------------------|
| `memory/pixel/ui-core.js` | manual CSS/JS panel work |

## Methodology

- **Score contribution** = weighted sum of (automations built × intervention-class weight) + (interventions avoided × 0.5)
- Weights: ops-elimination=1.2, monitoring=1.0, tracking=0.8, content=0.6
- Interventions still received reduce contribution (each = -0.3)
- Composite should approximate the autonomy score within ±5 points

## Bottleneck

Lowest contributor: **Pixel** (2.8). Gap to top: 6.3 points. Primary gap: fewer autonomous automations deployed in this agent's domain.