# Blocker Resolution Trends
Generated: 2026-11-23 06:21

## Summary
- **Total blockers tracked:** 15
- **Status breakdown:** open_needs_human: 10, ops_note: 1, reconciled: 1, resolved: 1, unknown: 2
- **Avg resolution time (dated pairs):** 48.0h
- **Range:** 48.0h - 48.0h

## Blockers by Agent
- **Orchestrator:** 5 total, 1 resolved/reconciled
- **Verifier:** 2 total, 0 resolved/reconciled
- **Builder:** 1 total, 0 resolved/reconciled
- **Designer:** 1 total, 0 resolved/reconciled
- **Researcher:** 1 total, 0 resolved/reconciled
- **Mechanic:** 1 total, 0 resolved/reconciled

## Blocker Classes (top 10)
- `winerror 10013`: 2
- `seat-unreachable + sandbox egress wall`: 1
- `helper down`: 1
- `helper file-not-found`: 1
- `file-absent`: 1
- `sandbox egress block`: 1
- `no browser binary + sandbox egress block`: 1
- `sandbox limitation`: 1
- ``schtasks` -> "error: class not registered"`: 1

## Currently Open (NEEDS-HUMAN)
- Orchestrator: elev.py PRESENT but helper DOWN (exit 5) (Orchestrator) [2026-11-20]
- Orchestrator #1 Live Hotload Execution: elev.py ABSENT on this seat (Orchestrator) [2026-11-20]
- Verifier #4 Performance Regression Gate: live-measurement leg blocked by :8099 egress wall (Verifier) [2026-11-20]
- #3 Build-Verify-Pin: memory_mirror.py is 0 bytes in sandbox (Builder) [2026-11-20]
- Goal #4 load-probe: Red sandbox cannot reach White:8099 (repeated across passes) [2026-11-17]
- Live-browser verification unavailable from this sandbox seat (Designer #5 + #7) (Designer) [2026-11-17]
- Verifier goal #2 SLO scheduled task: schtasks COM unavailable + egress block in sandbox (Verifier) [2026-11-17]
- Mirror-revert data collection (Researcher goal #3) [NEEDS-HUMAN] (Researcher)
- Mechanic #4 FleetBootRecovery schtask: COM wall on all sandbox seats (Mechanic) [2026-11-18]
- Orchestrator #2 Execute Engine: sandbox cannot reach Studio :8888 (Orchestrator) [2026-11-18]

## Resolved Blockers (with timing)
- 48.0h | None | White SANDBOX seat cannot LAN-probe Red .245 (confirmed)
- 48.0h | Designer | Live-browser verification unavailable from this sandbox seat (Designer #5 + #7)

## Insights & Recommendations
1. Most frequent blocker class: **winerror 10013** (2 occurrences). Consider a standing runbook or automation for this pattern.
2. **Orchestrator** has the most open blockers (3). Focus unblocking effort there first.
3. Average resolution time is 48.0h. Target: reduce to <48h by prioritizing oldest open blockers first.