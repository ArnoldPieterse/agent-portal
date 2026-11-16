# Self-Certification Audit v2 - RE-RUN (2026-11-16 06:22 UTC)

**Result: 106/234 = 45% clean** (baseline 48%, target >=90%)

| Agent | Clean/Total | Rate | Status |
|-------|-------------|------|--------|
| 2026-11-13-agent-goals | 23/60 | 38% | CRIT |
| INDEX | 0/0 | N/A | CRIT |
| all-goals-2026-11-13 | 29/80 | 36% | CRIT |
| archivist | 9/10 | 90% | OK |
| builder | 10/10 | 100% | OK |
| cycle2-dependency-map | 0/8 | 0% | CRIT |
| cycle2-kickoff-2026-11-16 | 0/6 | 0% | CRIT |
| designer | 4/10 | 40% | CRIT |
| designer-goal2-ops-tiers | 0/0 | N/A | CRIT |
| mechanic | 6/10 | 60% | WARN |
| orchestrator | 9/10 | 90% | OK |
| researcher | 5/10 | 50% | WARN |
| researcher-log-2026-11-13 | 0/0 | N/A | CRIT |
| scribe | 6/10 | 60% | WARN |
| verifier | 5/10 | 50% | WARN |

## Trend
| Run | Date | Clean/Total | Rate |
|-----|------|-------------|------|
| v2 initial | 2026-11-16 15:17 | 71/147 | 48% |
| v2 re-run | 2026-11-16 06:22 | 106/234 | 45% |

## Flagged Items (first 3 per agent)

### 2026-11-13-agent-goals
- `#1: Portal health via on-disk evidence each round start (canary JSON, file mtimes) +`
- `#2: Runbook-notes.md as the one-line log of what broke / what fixed it: every fix or`
- `#4: Mirror health: verify mirror_canary_result.json fresh (mirror_ok true, lag <600s`

### all-goals-2026-11-13
- `#4: Execute the backend-swap procedure (unload idle → load required model → restore `
- `#5: Commit via `POST /api/git` at every major milestone so uncommitted drift never e`
- `#7: Collect all seven goal lists next round and append them under `## AGENT GOALS (s`

### archivist
- `#6: Multi-host documentation consistency check - extract host-specific factual claim`

### cycle2-dependency-map
- `#1: **SLO pipeline** — Mechanic#4 (load baseline, daily jsonl) -> Builder#8 (/api/pe`
- `#2: **Fleet-state endpoint** — Mechanic#8 (GET /api/health/fleet) -> Builder#6 (pari`
- `#3: **Supersession validator** — Archivist#5 (script `archivist/supersession_check.p`

### cycle2-kickoff-2026-11-16
- `#1: **SLO pipeline** split into one capability / three roles: Mechanic#4 measures ba`
- `#2: **Fleet-state endpoint** owned by Mechanic#8 (GET /api/health/fleet); Builder's `
- `#3: **Supersession validator** dedup: script = Archivist#5, policy + weekly runs = S`

### designer
- `#2: Dark mode + theme toggle - persistent light/dark driven by the token layer, head`
- `#5: Breakpoint regression automation (replaces the original <768px responsive goal -`
- `#6: Status indicator system - consistent .status-dot component (green/amber/red + la`

### mechanic
- `#1: Adaptive fleet probe - upgrade fleet_probe.py from fixed 10-min cadence to trend`
- `#4: Portal load test & capacity baseline (SLO pipeline, Mechanic role) - daily probe`
- `#5: Change-entity health integration - probe output wired into the evolution layer: `

### orchestrator
- `#5: Milestone risk register - per-milestone risks + mitigations + owners for the cyc`

### researcher
- `#1: Automated claim-verification pipeline - re-run load-bearing factual claims on a `
- `#3: Fleet model benchmark study - Qwen3.8 variants (Q4_K_S vs Q8_0) measured on port`
- `#6: Sandbox-vs-host ground-truth daily diff - daily hash-diff of the shared allowlis`

### scribe
- `#2: Contradiction detector - automated cross-check of a round's claims (numbers/size`
- `#5: Supersession-chain integrity (policy owner per charter) - consume Archivist#5's `
- `#7: Owner-coverage ledger with API - standing map of every open TODO item -> exactly`

### verifier
- `#2: Fault injection suite - 5+ chaos scenarios (kill mid-request, corrupt files, dro`
- `#3: Evidence hash chain - SHA256-chained verification log, tamper-evident from genes`
- `#7: Evolution state machine validator - attempt every illegal CHG transition; confir`
