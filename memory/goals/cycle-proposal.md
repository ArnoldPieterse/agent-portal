# Next-cycle proposal (pre-computed by forecast engine)

Generated: 2026-11-25 09:51:00. Ratify/edit when the current cycle completes - do not draft cold. Ranked by predicted value: backlog cadence goals first, then successor patterns of just-closed work.

1. **[archivist] ARCHIVIST#6** - Knowledge decay model productionization - run decay_score.py weekly (scheduled task); auto-archive leaves scoring <0.2 (move to memory/archive/ with a pointer l (source: scheduled-background)
2. **[archivist] ARCHIVIST#8** - Snapshot diff weekly report - extend cycle-2 snapshot.py to produce a human-readable weekly diff summary: "X new leaves, Y modified, Z archived, W orphans creat (source: scheduled-background)
3. **[mechanic] MECHANIC#1** - Portal load test completion (cycle-2 #4 carryover) - the load probe needs 7 days of data; if the schtask was registered, collect remaining days + run --week-com (source: scheduled-background)
4. **[mechanic] MECHANIC#2** - Self-healing mirror productionization - the cycle-2 auto-repair design should now be a running scheduled task (every 15 min): detect missed syncs, re-sync autom (source: scheduled-background)
5. **[mechanic] MECHANIC#6** - Scheduled-task dependency graph productionization - the cycle-2 blast-radius map should now be auto-generated from schtasks /query output (run weekly); diff aga (source: scheduled-background)
6. **[mechanic] MECHANIC#8** - Chaos drill productionization (monthly) - the cycle-2 weekly chaos drill should now be a monthly scheduled task: kill portal on a rotating host, verify recovery (source: scheduled-background)
7. **[scribe] SCRIBE#10** - Scribe self-audit: compression fidelity score - for each synthesis produced in cycle 3, score "how much information was lost vs the source thread" (manual spot- (source: scheduled-background)
8. **[verifier] VERIFIER#8** - Mirror-sync drift detector productionization - the cycle-2 SMB drift detector should now run as a scheduled task (every 30 min); log all drift events; auto-aler (source: scheduled-background)
9. **[verifier] VERIFIER#8** - schtask `PortalSmbDrift` registered (30 min). Remaining: two weeks of drift-log review. (source: scheduled-background)
10. **[mechanic] MECHANIC#2** - schtask `MirrorHeal` registered (15 min). Remaining: two drift-free weeks (~02-12). (source: scheduled-background)
