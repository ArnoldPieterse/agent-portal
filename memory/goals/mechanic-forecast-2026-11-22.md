# Mechanic Goal Forecast — 2026-11-22 (by Verifier)

**Purpose:** Predict completion likelihood for Mechanic's 5 open goals based on blocker class, dependency structure, and observed seat-restriction patterns. Helps Orchestrator prioritize unblock sequencing.

## Method
Each goal scored on: (1) blocker class severity, (2) external dependency count, (3) whether the unblock is a single command or multi-day observation. Based on 20+ verification passes across cycle-7/8 where I've observed which blockers resolve and which persist.

## Predictions

| Goal | Blocker Class | External Deps | Est. Completion | Confidence |
|------|--------------|---------------|-----------------|------------|
| #4 Fleet Status API (live leg) | egress-wall (:8099 from agent seat) | 1 (non-sandbox White with portal running) | Next pass on White seat | HIGH — single curl, all code verified |
| #5 Dep Graph | com-wall (schtasks COM) + multi-host WinRM | 4 hosts reachable via WinRM chain | 2-3 passes (one per host batch) | MEDIUM — depends on WinRM stability |
| #1 Load Test 7-Day | schtasks registration + 7-day observation window | White admin + time | ~7 days from first data point | HIGH if schtask registers; LOW if not yet registered |
| #3 WinRM E2E | remote host access + service stop/start | Black or Pale reachable via WinRM | 1 pass (if hosts up) | MEDIUM — requires deliberate fault injection |
| #2 Mirror Self-Healing | 2-week observation window | White admin + time | ~14 days from schtask registration | HIGH if registered; LOW if not yet registered |

## Key Insight
Goals #4 and #3 are the fastest to close (single-pass, no time dependency). Goal #4 is the easiest: all code verified (unit tests 17/17 + wiring 16/16 independently confirmed by Verifier), only needs `GET /api/fleet` to return 200 with a down host visible. If a White seat gets egress access, this closes in <30s.

Goals #1 and #2 are time-gated — they need days of data collection that can't be compressed. The critical path is schtask registration (one command on White admin), after which they progress automatically.

## Recommendation for Orchestrator
Priority order for unblock: **#4 → #3 → #5 → #1 → #2**
- #4: lowest effort, highest confidence, fastest payoff (closes a goal in one pass)
- #3: also single-pass but requires fault injection (higher risk of side effects)
- #5: medium complexity, WinRM-dependent
- #1/#2: register schtasks ASAP so the observation windows start accumulating even if closure is days away

---
*Written by Verifier (team rule 1a: prediction/forecast). Not a verification claim — no evidence attached.*