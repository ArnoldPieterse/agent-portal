# Mechanic - Cycle 16 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Cycle Transition, (2) Self-Validation Circuit, (3) Adaptive Topology

1. **Seat Probe Scheduler** - memory/mechanic/seat_probe.py: every 5min probe all 8 seats; update seat-matrix.json state+last_seen; >30min unreachable triggers cascade. Verified: healthy=fleet all ready; killed process detected <5min. (pointer: memory/mechanic/MEMORY.md)

2. **Model Load Orchestrator** - memory/mechanic/model_orchestrator.py: coordinate model load on return: check VRAM, load, verify alias responds, update seat-matrix. Verified: full sequence <5min; matrix updated; alias confirmed. (pointer: memory/mechanic/MEMORY.md)

3. **Auto-Recovery Playbook v2** - extend playbooks with seat-unreachable: probe confirms down, attempt restart, check host health, if host down mark cascade+notify. Verified: simulated seat-down triggers full playbook; steps logged with timestamps.

4. **VRAM Budget Manager** - memory/mechanic/vram_budget.py: track per-host VRAM allocation; before load verify total<90%; suggest LRU unload if not. Verified: full host refuses+suggests; partial allows. (pointer: memory/mechanic/MEMORY.md)

5. **Fleet Topology Map** - memory/mechanic/topology_map.py: generate hosts->agents->models->tasks map from seat-matrix; update on change. Write to memory/ops/topology-map.json. Verified: reflects current state; updates after simulated move. (pointer: memory/mechanic/MEMORY.md)

6. **Health Score Computation** - memory/mechanic/health_score.py: 0-100 from seat availability(40%)+VRAM headroom(20%)+loop freshness(20%)+error rate(20%). Write to memory/ops/health-score.json. Verified: all-good>90; one-down+high-VRAM<60.

7. **Scheduled Task Health Check** - memory/mechanic/schtasks_health.py: verify all schtasks running (last-run within interval); flag stale; auto-restart if possible. Verified: healthy=0 flags; stale detected+restart attempted. (pointer: memory/mechanic/MEMORY.md)

8. **OOM Prevention Guard** - memory/mechanic/oom_guard.py: pre-load check predicted VRAM vs available; >95% blocks+alerts. Pre-hook for model_orchestrator. Verified: 96% used blocks; 50% allows. (pointer: memory/mechanic/MEMORY.md)

9. **Fleet Recovery Time Tracker** - measure detection-to-recovery time per incident type; track in memory/ops/recovery-times.jsonl; weekly mean+p95. Verified: 3 simulated incidents logged with correct durations.

10. **Autonomous Ops Decision Log** - log every autonomous ops decision (load/unload, re-route, restart) to memory/ops/auto-ops-decisions.jsonl with timestamp+trigger+outcome. Verified: 5 decisions = 5 entries; all fields populated.
