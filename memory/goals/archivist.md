# Archivist — Cycle 17 Goals (set 2026-11-24) [seat-drafted]
Round topic: **Fleet Self-Optimization & Steady-State Convergence**
Pillars: Predictive Ops / Adaptive Resources / Convergence Metrics

1. **Convergence Knowledge Base Entry** - create memory/archivist/convergence-kb.md defining steady-state criteria, autonomy score formula, convergence metrics glossary with file citations.
2. **Cycle History Index v2** - extend archive INDEX.md with structured metadata per cycle: topic, duration, completion %, key outcomes, interventions. Searchable by any field.
3. **Provenance Chain for Convergence Data** - for each metric value trace full provenance (agent, source data, timestamp). Store as memory/archivist/provenance-convergence.jsonl. (pointer: memory/archivist/provenance_ledger.py)
4. **Cross-Cycle Pattern Archive** - compile all pattern reports into single reference: memory/archivist/cross-cycle-patterns.md. Deduplicate; highlight emerging trends across cycles. (pointer: memory/archivist/evidence-stale-designer-cycle11-pointer-closed-2026-11-24.md)
5. **Steady-State Definition SSOT** - formal document defining steady-state: exact criteria, measurement methodology, entry/exit conditions, expected behavior. Referenced by all agents.
6. **Intervention Knowledge Graph** - graph of human interventions: who/which agent/type/outcome. Identify patterns (most-intervened agents, common types). Output: intervention-graph.json + summary. (pointer: memory/archivist/knowledge-graph-v3.json)
7. **Cycle Topic Evolution Timeline** - document topic evolution across cycles: proposed, selected, rationale. Identify coverage gaps. Output: memory/archivist/topic-evolution.md.
8. **Convergence Metric Lineage** - for each dashboard metric document full computation lineage: raw source -> transforms -> final value. Enables debugging/audit. Output: metric-lineage.md.
9. **Fleet Decision Archive** - compile autonomous decisions (ops + dispatch) into searchable archive with categories/outcomes. Identify good vs bad decision patterns. Output: decision-archive.md.
10. **Steady-State Readiness Assessment** - weekly assessment of convergence readiness: score each criterion, identify gaps, suggest next actions. Output: memory/archivist/readiness-assessment.jsonl.
