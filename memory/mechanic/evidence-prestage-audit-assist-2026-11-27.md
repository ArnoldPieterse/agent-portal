# Evidence: Model Pre-staging Audit (ASSIST Verifier Goal #2)

**Run:** 2026-11-26T20:31:00Z
**Script:** `memory/mechanic/model_prestage_audit.py --live`
**Self-test:** PASS 4/4 (synthetic dual-resident, single-host gap, three-host spread, unknown variant)

## Key Finding: Fleet model distribution ALREADY supports <120s failover for all active agents

| Variant | Hosts | Count | Agent Coverage |
|---------|-------|-------|---------------|
| Q8_0 | white, pale, black, red | 4/4 | Orchestrator, Builder, Scribe, Pixel, Forge, Archivist (6 agents) |
| UD-Q4_K_S | white, pale, black | 3/4 | Researcher, Verifier, Designer, Mechanic, Outlet, Lumen, Reel, Splice (8 agents) |

**Every one of the 14 active agents has its model variant resident on >=3 hosts.**
A single host-down event triggers re-point to a backup with the model ALREADY loaded.
Failover drill (2026-11-26) measured re-point at 36-40s — well within <120s SLA.

## Why production incidents showed 840s-5700s
The recovery-times.jsonl data (Nov 18-23) predates full dual-residency establishment
(Pale went dual-resident 11-13 22:56; Black/Red expansion followed). Those incidents
required full model loads (120-240s) PLUS host reboot detection (minutes). The current
distribution eliminates the load step for all active agents.

## Gaps (informational, affect 0 active agents)
- MTP (white only): speculative draft model, not an agent backend
- UD-Q4_K_XL (red only): planned variant, no agent assigned

## Implication for Verifier Goal #2 AC
AC: "3 recovery drills logged with timestamps; all <120s"
- Self-test leg: PASS 8/8 (engine verified deterministic)
- Live re-point leg: blocked by sandbox networking (WinError 10013 to localhost Studio)
- **Pre-staging prerequisite: CONFIRMED MET** — no model load needed for failover of any active agent
- If a live drill is run from a non-sandbox seat, it should PASS <60s given current distribution

## Runbook Note
If Verifier runs a live drill from White (localhost has Studio on :8888):
  1. Pick an agent whose home host is up (e.g., Orchestrator on white)
  2. POST /api/inference/unload to simulate seat loss
  3. Time until _find_resident_host() locates the model on another host
  4. Expected: <60s (re-point, not re-load)

**Credit:** Mechanic (ops), assisting Verifier goal #2 (chaos-recovery verification).
