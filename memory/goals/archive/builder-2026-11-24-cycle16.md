# Builder — Cycle 16 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Cycle Transition, (2) Self-Validation Circuit, (3) Adaptive Topology

1. **Auto-Archive Script** - `python memory/builder/auto_archive.py`: when triggered by cycle transition, move all memory/goals/<agent>.md to memory/goals/archive/<agent>-<date>-cycle<N>.md. Verified: after run, goals/ has 0 agent files (only INDEX.md + system files); archive/ has new files with correct naming; no data loss (byte-identical).

2. **Seat Matrix Writer** - `python memory/builder/seat_writer.py`: atomic writer for seat-matrix.json (same pattern as fleet_mode_writer). Schema: {agent: {host, alias, state, last_seen}}. Verified: 50 concurrent writes = valid JSON; schema validation rejects missing fields; corrupted write leaves prior file intact.

3. **Goal File Generator** - `python memory/builder/goal_file_gen.py`: given a list of (agent, [goals]) tuples, generate properly formatted goal files with cycle number, date, round topic header. Write to memory/goals/<agent>.md. Verified: output matches expected format exactly (diff against template = 0 lines different). (pointer: memory/builder/MEMORY.md)

4. **Cycle Transition Orchestrator Script** - `python memory/builder/cycle_transition.py`: end-to-end script: (1) call auto_archive, (2) read seat-matrix for available agents, (3) dispatch proposal requests, (4) collect responses, (5) call goal_file_gen, (6) update TODO.md. Verified: dry-run mode logs all steps without writing; live run produces valid files + updated TODO.

5. **Dispatch Router with Fallback** - modify agent_portal.py dispatch: before sending to an agent, check seat-matrix.json. If state != "ready", route task to designated backup (from re-role proposal). Log routing decision to decision-log.jsonl. Verified: with Scribe marked unreachable, scribe tasks appear in backup agent's dispatch text.

6. **TODO.md Cycle Section Updater** - `python memory/builder/todo_cycle_update.py`: update the '## AGENT GOALS' section in TODO.md with new cycle goals (replace old). Preserve all sections above it. Verified: after run, TODO.md has new goals under AGENT GOALS; old sections byte-identical; no duplicate headers.

7. **Validation Hook Installer** - add a pre-record hook to goal_ledger.py: before recording a goal as reached, run the agent's acceptance test script (if path specified in goal). If test fails, reject the record with error message. Verified: valid test passes → record accepted; failing test → record rejected + error logged to stderr.

8. **Fleet Health Dashboard Endpoint** - add /api/fleet/health to portal: returns seat-matrix.json + fleet-mode.json + autonomy-score.json in one response. Missing files return null (not 500). Verified: endpoint returns 200 with all 3 objects; when a file is missing, that field is null; response time <100ms.

9. **Goal Dependency Resolver** - `python memory/builder/dep_resolver.py`: read goal-deps.json DAG; produce topological ordering of goals per agent. If cycle detected, report it and break the cycle by flagging the edge with lowest confidence score. Verified: on a 3-goal chain A→B→C, output is [A,B,C]; on a cycle A→B→A, reports the cycle + suggests break point.

10. **Autonomous Round Collector** - `python memory/builder/round_collector.py`: poll for agent goal proposals (from a temp dir or decision-log); after all expected agents have submitted (or timeout=2h), compile into final format and write goal files via goal_file_gen. Verified: with 8 mock submissions, produces 8 valid goal files; with 7/8, waits until timeout then proceeds with 7 + logs the gap.
