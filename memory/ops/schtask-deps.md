# Scheduled-Task Dependency Graph (Blast Radius)
Last updated: 2026-11-16 ~14:10 (Mechanic goal #7 cycle 2)
Source: memory/ops/host-port-task-map-2026-11-15.md + fleet_probe_v2.py target set

## Task Inventory (5 unique tasks x up to 4 hosts)

| Task | Hosts | Schedule | Script/Action |
|---|---|---|---|
| PortalRun | White, Red, Pale, Black | At logon | agent_portal.py (PID in _portal_pid.txt) |
| MemoryMirrorRun | White only | Every 5 min | memory_mirror.py (push/pull allowlist to remotes) |
| PortalDailyGitCommit | White only | Daily 18:00 | POST /api/git (safety-net commit) |
| PortalFleetProbe | White only | Every 10 min | fleet_probe_v2.py (4-host port + latency) |
| RecoverAll | White, Red, Pale, Black | On demand / boot | recover_all.py (model reload per llm recipe) |

## Dependency Edges (A depends on B = A breaks if B fails)

```
PortalRun(White)
  ├── PortalDailyGitCommit   [POST /api/git needs :8099]
  ├── All agent group chat    [/api/runs, /api/goals, /api/memory all via portal]
  ├── Fleet health endpoint   [GET /api/health/fleet if goal #8 ships]
  └── Load test (goal #4)     [white_load_q8.py targets :8099]

PortalRun(Red|Pale|Black)
  └── Remote agent seats      [Scribe/Mechanic on Red, Designer/Archivist on Pale, Builder/Verifier on Black]

MemoryMirrorRun(White)
  └── Remote memory freshness [stale files on remotes; agents see missing/old content]
      └── Indirect: goal tracking, TODO.md sync, evidence leaves

PortalFleetProbe(White)
  └── Outage early-warning    [no direct breakage, but CRIT events feed:
      ├── Change-entity creation (goal #5)
      ├── Chaos drill detection (goal #9)
      └── Fleet health endpoint freshness (goal #8)]

RecoverAll(White|Red|Pale|Black)
  └── Model residency         [LM Studio :8888 must have model loaded for agent to respond]
      └── Agent availability  [404 = agent silent; saw Orchestrator+Researcher today]
```

## Blast-Radius Scenarios

### Scenario 1: PortalRun(White) fails (portal down)
**Direct impact:** ALL agents lose group chat, API access, goal tracking.
**Cascading:** PortalDailyGitCommit no-ops (403/timeout), load test impossible, fleet endpoint dead.
**Recovery:** `taskkill /PID <_portal_pid.txt>` then `schtasks /run PortalRun` or manual `python agent_portal.py`.
**RTO target:** <5 min (goal #1 cycle 1 standard).

### Scenario 2: MemoryMirrorRun(White) fails
**Direct impact:** Remotes see stale memory; White sees stale remote state.
**Cascading:** Agents on remote seats may reference missing files; TODO.md divergence.
**Recovery:** Manual `python memory_mirror.py` forces full push/pull cycle.
**Detection gap:** No alert currently (cycle 2 goal #3 adds self-healing).

### Scenario 3: PortalDailyGitCommit fails
**Direct impact:** No safety-net commit for the day.
**Cascading:** If disk failure or accidental deletion, up to 24h of work lost.
**Recovery:** Manual `POST /api/git` or `git add -A && git commit`.
**Severity:** LOW (24h window, local files still intact).

### Scenario 4: PortalFleetProbe fails
**Direct impact:** No visibility into remote host health; outages undetected.
**Cascading:** Change-entity creation (goal #5) stops; chaos drill (goal #9) can't detect recovery.
**Recovery:** Manual `python fleet_probe_v2.py white` or wait for next scheduled run.
**Severity:** MEDIUM (no direct breakage but removes early warning).

### Scenario 5: RecoverAll fails on a remote host
**Direct impact:** Model not loaded in VRAM; agent seat returns 404.
**Cascading:** That agent is silent for the entire group run cycle.
**Recovery:** `python recover_all.py` on that host (via WinRM or RDP).
**Severity:** HIGH (agent unavailable = lane blocked).

## Cycle-2 Gaps (what to build)
1. **Boot-detection task** (goal #2): After PortalRun starts, auto-trigger RecoverAll if model not resident within 30s.
2. **Self-healing mirror** (goal #3): MemoryMirrorRun failure detection → auto re-sync within 5 min.
3. **Chaos drill** (goal #9): Weekly kill+verify of PortalRun on rotating host; validates recovery path under live conditions.
4. **Fleet endpoint** (goal #8): Single API call replaces manual schtasks queries for status checks.
