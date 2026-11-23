# Mechanic - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes fleet ops self-sustaining: automatic recovery, predictive maintenance, and zero-touch failover.

1. **Host Health Auto-Recovery** - `python memory/mechanic/auto_recover.py`: when a host fails health check (from probes), automatically attempt recovery in order: (1) restart service via WinRM, (2) reboot host, (3) fail over to backup host. Log each step + outcome. Verified: 2 simulated failures trigger auto-recovery; recovery succeeds within 5 min for service restart; failover triggers when reboot fails; all steps logged with timestamps.

2. **Predictive Maintenance Scheduler** - `python memory/mechanic/predictive_maint.py`: based on historical failure patterns (from incident logs), schedule preventive actions: disk cleanup before full, model reload before OOM pattern, cache clear before memory pressure. Emit maintenance schedule to memory/mechanic/maintenance-<date>.md. Verified: >=3 predictive rules defined; a disk at 85% triggers cleanup before 95%; schedule shows next 7 days of planned actions.

3. **WinRM Connection Pool** - `python memory/mechanic/winrm_pool.py`: maintain a pool of WinRM connections to all hosts; auto-reconnect on failure; measure connection latency; alert if any host is unreachable for >60s. Emit connection stats to memory/mechanic/winrm-stats-<date>.json. Verified: 3 hosts connected; a simulated disconnect triggers reconnect within 30s; latency p95 <500ms; alert fires on sustained unreachability.

4. **Model OOM Auto-Swap** - `python memory/mechanic/oom_swap.py`: when VRAM usage exceeds 90% on any host, automatically: (1) identify the least-critical loaded model, (2) unload it, (3) log the swap decision, (4) notify Orchestrator. Verified: simulated OOM triggers swap; correct model is selected (lowest priority); swap completes in <30s; Orchestrator receives notification.

5. **Network Partition Detection** - `python memory/mechanic/net_partition.py`: detect when a host becomes network-partitioned (reachable via ping but not via WinRM, or vice versa); distinguish from full outage; trigger appropriate response (retry vs failover). Verified: 2 partition scenarios tested; correct diagnosis in both; response action matches the diagnosis; detection latency <60s.

6. **Fleet Resource Balancer** - `python memory/mechanic/resource_balancer.py`: monitor VRAM + CPU + disk across all hosts; when imbalance exceeds threshold (e.g., one host >70% while another <30%), recommend or execute migration of workloads. Emit balance report. Verified: >=3 resources monitored; an imbalanced state is detected; a recommended migration is computed; execution moves workload and rebalances within 10%.

7. **Incident Post-Mortem Auto-Gen** - `python memory/mechanic/postmortem_gen.py`: after any incident (detected via health check failure + recovery), auto-generate a post-mortem: timeline, root cause hypothesis, impact scope, actions taken, prevention recommendations. Emit memory/mechanic/postmortem-<date>.md. Verified: 2 incidents produce post-mortems; each has all 5 sections; timeline is chronologically correct; prevention recommendation is actionable.

8. **Scheduled Task Monitor** - `python memory/mechanic/schtasks_monitor.py`: monitor all scheduled tasks (schtasks) in the fleet: are they running on schedule? Did any fail? Is any overdue? Alert on failure or >2x expected interval. Emit monitor report. Verified: >=5 tasks monitored; a deliberately failed task is detected within 1 pass; an overdue task is flagged; report shows next-run time for each.

9. **Fleet Topology Map** - `python memory/mechanic/topology.py`: maintain a live map of fleet topology: which agents run on which hosts, which models are loaded where, network connections between hosts. Emit memory/mechanic/topology-<date>.json + visual (ASCII or SVG). Verified: map shows all 4 hosts + 8 agents; model assignments match actual state; a host going down is reflected in <60s; topology is machine-readable.

10. **Auto-Scale Simulation** - `python memory/mechanic/scale_sim.py`: simulate fleet scaling scenarios: (a) add a new host, (b) lose a host, (c) double the workload. For each, compute: can current fleet handle it? What would need to change? What's the cost? Emit simulation report. Verified: 3 scenarios simulated; each has a verdict (handle/upgrade/fail); resource math is correct; recommendations are specific (e.g., "move Researcher to host X").
