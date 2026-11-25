# Fleet Autonomy Playbook
*Last updated: 2026-11-25 (cycle 23) | Score: 71.3/100*

## What the fleet does autonomously now

| Capability | Automation | Evidence |
|---|---|---|
| Portal crash recovery | `memory/mechanic/portal_watchdog.py` + `memory/ops/boot_recovery.py` (schtasks) | autonomous-actions.jsonl: restart_portal, outcome=success |
| Fleet probe & health check | `memory/ops/fleet_probe_v2.py` (scheduled) | 4-host model load detection, auto-relocation |
| Mirror sync healing | `memory/ops/mirror_heal.py` + scheduled task | Auto-detects and fixes pin-file clobber loops |
| Pointer/index integrity | `memory/archivist/index_check.py` | Dangling/orphan/stale pointer detection (44/44 verified) |
| Goal lifecycle tracking | `memory/researcher/goal_ledger.py` + `/api/goals` | Auto-record verified completions, dashboard counts |
| Cycle duration tracking | `memory/ops/cycle-durations.jsonl` | Auto-measured per cycle |
| Autonomy score computation | `memory/orchestrator/autonomy_score.py` | 4-component weighted composite, auto-updated |
| Convergence readiness assessment | `memory/scribe/convergence-readiness.md` | 8-criteria checklist, auto-evaluated |
| Decision logging + traceability | `memory/synthesis/decisions.jsonl` + decision-autonomy-map | Full chain: decision -> automation -> intervention removed |
| Chaos drill (recovery testing) | `memory/ops/chaos_drill.py` + scheduled task | Periodic kill-restart validation |
| Disk space management | auto_clean_disk action | autonomous-actions.jsonl entry |
| Canary deploy | deploy_canary action | autonomous-actions.jsonl entry |

## Where human input is still needed

| Intervention class | Count (lifetime) | Reason it persists | Path to elimination |
|---|---|---|---|
| **Approve** (goal-set ratification) | 3/10 | Fleet cannot self-ratify its own goal set without circular authority | Decision: define N-cycle auto-approve threshold for low-risk goals |
| **Redirect** (priority/priority change) | 3/10 | Human sets strategic direction; fleet optimizes within it | Unavoidable by design — human is the goal-setter |
| **Unblock** (resolving blockers) | 4/10 | Model relocation, UI bug fixes that require judgment | Partially addressed: model relocation now auto-detected; UI bugs still need human spec |

### Specific remaining gaps:
1. **UI acceptance criteria** — Human must specify "what looks right" for visual elements (cycle 15: button sizing/placement). *Path: build a design-rubric auto-checker.*
2. **Model seat relocation** — When a host goes down, fleet detects it but the "treat as normal seat" confirmation still comes from human (cycle 17). *Path: codify auto-relocation policy in fleet-mode.json.*
3. **Goal-set approval** — Each cycle's goal set needs human sign-off before work begins. *Path: define confidence threshold for auto-approve (e.g., all goals P>0.8 from forecast).*

## Score trajectory
| Cycle | Score | Delta | Key driver |
|---|---|---|---|
| 5 | 64.5 | — | Baseline (derived) |
| 17 | 69.1 | +4.6 | Portal auto-recovery live, evolution CLI deployed |
| 23 | 71.3 | +2.2 | Duration improvement (mean 28h vs 48h baseline), rework stable |

**Trend: positive, no reversal flag.** Next inflection expected when intervention count drops below 5/cycle or auto-approve policy lands.
