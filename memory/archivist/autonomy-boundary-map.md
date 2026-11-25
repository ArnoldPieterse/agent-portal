# Autonomy Boundary Map
*Archivist goal #6 (cycle 18) | 2026-11-25*

Defines the exact boundary between **autonomous** (agent decides + acts) and
**human-in-the-loop** (agent proposes, human approves or redirects) per domain.

## Legend
- **A** = Autonomous: agent executes without human input
- **H** = Human-in-the-loop: agent prepares recommendation; human approves/redirects
- Confidence: **high** (observed >=3 cycles), **med** (1-2 cycles), **low** (inferred)

## Domain 1: Operations (ops)

| Decision | Boundary | Confidence | Last Validated |
|----------|----------|------------|----------------|
| Cycle plan drafting + execution | A | high | 2026-11-25 |
| Model load/unload on healthy hosts | A | high | 2026-11-25 |
| Model relocation (host down) | A | med | 2026-11-25 |
| Host reboot / power cycle | H | high | 2026-11-24 |
| New host provisioning | H | high | 2026-11-20 |
| Admin privilege escalation (elev.py) | A | high | 2026-11-25 |
| Scheduled task creation/modification | A | med | 2026-11-25 |

## Domain 2: Dispatch (agent-to-task matching)

| Decision | Boundary | Confidence | Last Validated |
|----------|----------|------------|----------------|
| Assign goal to agent per lane map | A | high | 2026-11-25 |
| Cross-agent assist (working another's goal) | A | med | 2026-11-25 |
| New agent onboarding (register + persona) | H | high | 2026-11-25 |
| Agent deactivation / removal | H | high | 2026-11-18 |
| Temperature/persona parameter changes | H | med | 2026-11-22 |

## Domain 3: Goal-Setting

| Decision | Boundary | Confidence | Last Validated |
|----------|----------|------------|----------------|
| Cycle goal drafting (per lane) | A | high | 2026-11-25 |
| Goal priority ranking within cycle | A | med | 2026-11-25 |
| Round topic selection | H | high | 2026-11-25 |
| Fleet-level goal (cross-lane) | H | med | 2026-11-24 |
| Goal closure (marking REACHED) | A | high | 2026-11-25 |
| Goal rejection / re-scoping mid-cycle | H | low | inferred |

## Domain 4: Model Management

| Decision | Boundary | Confidence | Last Validated |
|----------|----------|------------|----------------|
| Model selection per agent (from approved set) | A | med | 2026-11-25 |
| New model addition to approved set | H | high | 2026-11-20 |
| Model version upgrade | H | med | 2026-11-22 |
| OOM recovery / VRAM reallocation | A | high | 2026-11-25 |
| Model parameter tuning (temp, top_p) | H | high | 2026-11-22 |

## Domain 5: Publishing / External Output

| Decision | Boundary | Confidence | Last Validated |
|----------|----------|------------|----------------|
| Internal memory writes (any file in memory/) | A | high | 2026-11-25 |
| Portal UI changes (CSS/JS/HTML) | A | med | 2026-11-25 |
| Public upload / post to external platform | H | high | 2026-11-24 |
| Reply to external user message | H | high | 2026-11-24 |
| Repost / share of internal content externally | H | high | 2026-11-24 |

## Boundary Shifts (autonomy gained over time)

| Domain | Was | Now | Cycle Changed | Trigger |
|--------|-----|-----|---------------|---------|
| ops: model relocation | H | A | cycle 17 | Mechanic built auto-relocation script |
| dispatch: cross-agent assist | H | A | cycle 18 | Handoff protocol documented |
| goal-setting: priority ranking | H | A | cycle 18 | Forecaster engine (next10.json) |

## Escalation Rules (when A becomes H)

1. **Novelty**: If a decision type has no prior precedent in memory/ops/, default to H until 3 successful autonomous instances logged.
2. **Irreversibility**: Any action that cannot be undone without human intervention (data deletion, external publish, host formatting) is always H.
3. **Cost threshold**: Actions with estimated cost > $5 or > 1 GPU-hour require H approval.
4. **Safety**: Any action affecting physical hardware power state requires H.

## Validation Protocol

- Each boundary row is re-validated at cycle close by Archivist.
- If an agent acts autonomously on an H-boundary item, log as "boundary violation" in memory/ops/blockers.md.
- If a human intervenes on an A-boundary item 2+ times in 3 cycles, propose boundary shift to H (flag for next cycle review).

---
*Sources: autonomy-scorecard.json, convergence-lock-protocol.md, steady-state-ssot.md, human-interventions.jsonl, cycle logs c17-c18.*
