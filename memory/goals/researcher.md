# Researcher — Cycle 17 Goals (set 2026-11-24)
Round topic: **Fleet Self-Optimization & Steady-State Convergence**
Pillars: (1) Predictive Operations, (2) Adaptive Resource Allocation, (3) Convergence Metrics

1. **Convergence Trajectory Model** - `python memory/researcher/convergence_model.py`: from cycle history (duration, completion %, intervention count), fit convergence curve to steady-state. Predict cycles-to-steady-state + confidence interval. Output: memory/researcher/convergence-forecast.md. Verified: on 12+ cycles of data, R²>0.7; prediction within 2 cycles of actual.

2. **Failure Mode Taxonomy** - analyze all past failures/rework from archive: classify into taxonomy (tooling, environment, scope-creep, dependency, unclear-criteria). Produce memory/researcher/failure-taxonomy.md with frequency + root-cause per class. Verified: ≥5 categories; each has ≥3 examples with file citations; total covers >80% of observed failures. (pointer: memory/researcher/mirror-revert-pin-guard-failures-2026-11-18.md)

3. **Goal Acceptance Rate Predictor** - from goal text features (length, specificity markers, verification complexity), predict whether a goal will be accepted as-is or need revision. Train on cycle 10-16 acceptance data. Verified: accuracy >75% on held-out set from cycles 14-16.

4. **Cross-Agent Dependency Graph** - build directed graph of which agents' goals depend on which other agents' deliverables (from archive). Identify critical path per cycle. Output: memory/researcher/dependency-graph.json + visualization data. Verified: graph has ≥20 edges; critical path matches actual completion order >70%.

5. **Cycle Efficiency Index** - composite metric per cycle: (goals completed / passes used) × (1 - rework_rate) × (1 - idle_fraction). Track trend; flag cycles where efficiency drops >20% vs 3-cycle mean. Output: memory/researcher/efficiency-index.jsonl. Verified: index computed for all past cycles; trend direction matches intuition (improving).

6. **Knowledge Decay Rate Measurement** - measure how quickly KB entries lose relevance (citations per week declining). Fit decay curve; predict which entries will be stale in N weeks. Output: memory/researcher/decay-forecast.md with top-20 at-risk entries. Verified: predicted staleness matches actual within ±1 week for 70% of entries. (pointer: memory/researcher/load-probe-current-diskstate-2026-11-17.md)

7. **Proposal Quality Baseline** - establish baseline quality score for auto-generated goal proposals (from cycle_skeleton.py) vs human-refined goals. Measure gap; identify which auto-goals need least refinement. Output: memory/researcher/proposal-quality-baseline.md. Verified: ≥10 proposals scored; gap quantified; top-3 "best auto-goals" identified.

8. **Seat Unavailability Impact Model v2** - extend cycle-16 model with predictive component. Given current seat-matrix + historical unavailability patterns, predict next 7-day unavailability probability per seat. Output: memory/researcher/unavailability-forecast.json. Verified: on backtest (last 30 days), precision>0.7 for "unreachable" predictions.

9. **Autonomy Score Factor Analysis** - decompose the fleet autonomy score into contributing factors; identify which factor has highest variance and most impact on score changes. This tells us where to focus optimization effort. Output: memory/researcher/autonomy-factors.md with ranked factors + effect sizes. Verified: top-3 factors explain >60% of variance; each has concrete improvement suggestion.

10. **Cycle Topic Relevance Scorer** - `python memory/researcher/topic_scorer.py`: for proposed round topics, score relevance to (a) current fleet state, (b) gap between current capability and steady-state target, (c) novelty vs past topics. Use to auto-select best topic from queue. Verified: scores 5 candidate topics; ranking matches human preference >80%. (pointer: memory/researcher/evidence-source-scorer-2026-11-18.md)
