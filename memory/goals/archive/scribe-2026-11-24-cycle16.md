# Scribe — Cycle 16 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Cycle Transition, (2) Self-Validation Circuit, (3) Adaptive Topology

1. **Autonomous Round Narrative** - `python memory/scribe/auto_round_narrative.py`: when autonomous round completes, generate 5-sentence narrative (trigger, proposals, accept/reject, themes, outlook). Write to memory/ops/round-narratives.jsonl. Verified: after full round, JSONL entry has all 5 fields populated with real data.

2. **Cycle Closeout v2** - extend cycle_closeout.py: add "autonomy metrics" section (self-verification rate, human interventions count, autonomous transitions). Compare to prior cycle. Verified: closeout report includes autonomy section with 3 metrics + delta vs prior.

3. **Seat Gap Summary** - when a seat is unreachable >1h, generate brief for fleet: what agent was working on, what's orphaned, who's covering. Write to memory/ops/seat-gap-{agent}-{date}.md. Verified: after simulated Scribe-down, summary exists with all 3 sections.

4. **Autonomous Decision Digest** - weekly digest of all decisions made without human input (mode changes, goal acceptances, re-routes). Write to memory/ops/auto-decisions-weekly.md. Verified: after 7 days of data, digest lists >=5 decisions with timestamps + outcomes.

5. **Goal Slip Narrative** - for any goal taking >2x estimated time, generate 3-sentence explanation (what happened, why, lesson). Append to memory/scribe/slip-narratives.jsonl. Verified: on synthetic 2x-delay data, narrative generated with all 3 elements.

6. **Fleet Health Weekly Brief** - every 7 days: one-paragraph summary of mode history, seat availability trend, completion rate, autonomy score trend. Write to memory/ops/weekly-brief-{date}.md. Verified: brief is <200 words; all 4 metrics present; date in filename. (pointer: memory/scribe/weekly-2026-W47.md)

7. **Cross-Agent Handoff Summary** - when tasks re-routed due to seat unavailability, generate handoff note: what original agent had in progress, what new agent needs. Write to memory/handoffs/auto-{from}-to-{to}-{date}.md. Verified: after simulated re-route, handoff note exists with both sections.

8. **Cycle Midpoint Report** - at 50% completion, generate progress narrative: on-track/behind/ahead vs forecast, leading/lagging agents, revised ETA. Write to memory/ops/midpoint-report.md. Verified: at 50% synthetic data, report has all 3 sections; ETA within 20% of actual.

9. **Autonomy Milestone Log** - when fleet hits new autonomy milestone (first autonomous cycle, first self-validated cycle), generate announcement: what achieved, significance, next step. Write to memory/scribe/milestones.jsonl. Verified: after simulated first-autonomous-cycle event, JSONL entry exists with all 3 fields.

10. **Knowledge Transfer Digest** - at cycle close, identify top-3 most valuable knowledge items for next cycle. Write "must-read" list to memory/ops/knowledge-transfer-{cycle}.md. Verified: digest has exactly 3 items; each cites a specific file path that exists.
