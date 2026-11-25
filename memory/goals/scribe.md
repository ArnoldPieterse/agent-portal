# Scribe — Cycle 18 Goals (set 2026-11-25)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomy Measurement & Decomposition, (2) Intervention Elimination Tracking, (3) Convergence Velocity & Projection

1. **Autonomy Score Trendline** - Append each cycle's autonomy score + delta to memory/scribe/autonomy-trend.jsonl (timestamp, score, delta_from_prev, component_breakdown). Flag when 3-cycle rolling trend reverses direction. Verified: >=2 entries; delta math correct; reversal flag logic works on synthetic data.

2. **Convergence Readiness Checklist** - Living checklist of steady-state criteria (0 interventions for N cycles, self-healing rate >95%, cycle duration <48h, etc.); auto-update pass/fail status from fleet-mode.json + intervention log each cycle. Output: memory/scribe/convergence-readiness.md. Verified: >=5 criteria; at least 1 shows live pass/fail from source data.

3. **Decision-to-Autonomy Causal Map** - For each entry in decisions.jsonl that eliminated an intervention class, trace the chain: decision -> automation built (file path) -> intervention class removed -> autonomy score contribution. Output: memory/scribe/decision-autonomy-map.jsonl. Verified: >=3 causal chains; each file path exists.

4. **Fleet Autonomy Playbook** - Condensed two-page doc for the human: "what the fleet does autonomously now" (list) vs "where human input is still needed" (list with reason). Updated each cycle from intervention log + automation inventory. Output: memory/scribe/autonomy-playbook.md. Verified: both sections present; >=5 items in autonomous list; each human-input item has a reason.

5. **Intervention Pattern Classifier** - Auto-classify each human intervention into a pattern (misdiagnosis, preference override, new requirement, edge case, tool gap); compute per-pattern count + trend (declining/stable/emerging). Output: memory/scribe/intervention-patterns.jsonl. Verified: all interventions in log classified; >=3 distinct patterns identified; trend labels present.

6. **Convergence Velocity Report** - Measure convergence rate: interventions/cycle, new automations/cycle, autonomy score delta/cycle. Linear-regression ETA to steady-state (score >=90). Output: memory/scribe/convergence-velocity.md. Verified: >=3 data points used; ETA is a date; slope direction stated.

7. **Agent Autonomy Contribution Matrix** - Per agent: count of interventions their automation eliminated (from decision-autonomy-map), total autonomy score contribution, rank. Output: memory/scribe/agent-autonomy-matrix.md. Verified: all 10 agents listed; ranks sum correctly; top-3 identified.

8. **Convergence Anomaly Detector** - `python memory/scribe/convergence_anomaly.py`: compare current cycle metrics (autonomy score, intervention count, cycle duration) against 3-cycle rolling average; flag any metric deviating >20%. Append alert to memory/ops/anomalies.jsonl. Verified: script runs clean on real data; at least one threshold check executes; output format matches spec.

9. **Autonomy Handoff Protocol** - Document the protocol for when an agent's automation replaces a human step: required evidence (before/after metrics), recording format (which file, which field), verification criteria (N consecutive cycles without regression). Output: memory/scribe/autonomy-handoff-protocol.md. Verified: 3 sections (evidence, recording, verification); each has concrete example from existing data.

10. **Autonomy Score Decomposition** - Break the autonomy score into sub-components (self-healing rate, intervention ratio, cycle completion rate, forecast accuracy); track each independently per cycle; identify bottleneck component (lowest vs target). Output: memory/scribe/autonomy-decomposition.jsonl. Verified: >=4 components tracked; bottleneck identified with reasoning; values sum to or approximate the composite score.
