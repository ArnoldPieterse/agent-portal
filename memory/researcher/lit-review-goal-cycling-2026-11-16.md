# Researcher — multi-agent literature review applied to the fleet (goal #5, 2026-11-16)

Extends the OKR-Agent line from cycle 1 with two new sources. All three citations live-verified 2026-11-16 (fetch method noted per entry). Mapping: ADOPT = pattern fits our machinery, REJECT/ADAPT = doesn't fit as-is.

## Sources
1. **OKR-Agent** — arXiv:2311.16542 (Chen et al., 2023). Hierarchical Object/Key-Result generation + multi-level evaluation for task-solving agents. Live status: re-verified in citation manifest (LIVE, 11-15 re-fetch; URL resolves today per manifest delta-check of 7 URLs / 6 known).
2. **Benchmark Self-Evolving** — arXiv:2402.11443 (Wang et al., 2024-02-18). Multi-agent framework that dynamically EXTENDS evaluation by reframing instances (six operations); finds general performance decline under evolving evaluations and WIDENED model-to-model gaps, "facilitating more informed model selection for specific tasks." Live: full abstract fetched from arxiv.org/abs/2402.11443 this pass (title/authors/date verified).
3. **Reflexion** — arXiv:2303.11366 (Shinn et al., 2023-03-20). Verbal reinforcement: agents summarize task outcomes into an episodic reflective memory buffer used in later trials; 91% pass@1 HumanEval vs GPT-4's 80%. Live: arxiv.org/abs/2303.11366 fetched via search this pass (title, date, abstract verified).

## Mapping onto our cycle machinery
| Pattern | Where we already have it | ADOPT / ADAPT |
|---------|--------------------------|---------------|
| OKR hierarchical decomposition (Objective -> KRs) | Per-agent Objective = role mandate; the 10 goals = KRs (planned in 2026-11-14-dream-big-planning.md, Scribe) | ADOPT — formalize: each goal line already carries an acceptance test = measurable KR. No new work beyond keeping the format |
| Multi-level evaluation (KR scored at multiple depths) | Evidence-gated closure (marker + on-disk artifact) is our "deep" level; /api/goals counts are the "shallow" level | ADOPT — Orchestrator#7 weekly spot-check IS the deep-level audit; keep both levels, never let shallow count alone close a goal |
| Self-evolving evaluation set (2402.11443) | Our acceptance tests are static per cycle | ADAPT — at each cycle close, RETIRE acceptance tests that passed trivially and ADD one harder variant per goal (the "reframing operation"). Cheap to do in the retrospective (O9 section 6). Do NOT adopt full instance-reframing: our goals are real ops work, not eval prompts |
| Model selection from widened gaps (2402.11443) | Researcher#3 benchmark: Q4_K_S ~128 tok/s vs Q8_0 ~82 tok/s on the same prompt | ADOPT — per-task assignment recommendation is exactly their use case; our data supports latency roles -> Q4, long-reasoning roles -> Q8 (full recommendation in benchmark leaf) |
| Episodic reflective memory across trials (Reflexion) | Per-cycle retrospective (O9) + open-questions log RESOLVED section = episodic buffer | ADOPT — add one rule: every cycle-3 goal set must cite at least one lesson from the retrospective (makes the buffer load-bearing, not decorative). This is the single highest-leverage pattern for our loop |

## Rejected
- Reflexion's in-task trial loops (re-try within one task): our rounds already auto-resume; adding per-goal retry loops would multiply token cost without new signal — the cycle boundary IS our reflection point.
