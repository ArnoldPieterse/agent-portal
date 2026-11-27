# Autonomy Gap Audit (Verifier goal #9)
- generated 2026-11-26T13:31:51Z
- source: `memory\ops\blockers.md`
- entries total **19** | active **17** | closed **2**
- human-required **8** (47% of active) | automatable **9** (53%)
  - of which predate cycle start (2026-11-25): **7** (potentially stale; recommend one-time re-assessment sweep, NOT per-wall re-probe)
- target <10% human-required: **NOT MET**

## Per-entry classification
| # | tag | who | label | rationale |
|---|-----|-----|-------|-----------|
| 0 | OPS-NOTE | Researcher | **automatable** | agent-actionable unblock step present |
| 1 | OPS-NOTE |  | **human_required** | env/infra wall (sandbox egress), no agent path |
| 2 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (helper DOWN) with no agent-actionable step |
| 3 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (elev.py ABSENT) with no agent-actionable step |
| 4 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (WinError 10013) with no agent-actionable step |
| 5 | NEEDS-HUMAN | Builder | **automatable** | tag=NEEDS-HUMAN: operational/data note with a stated remediation, no hard env wall |
| 6 | RECONCILED | Orchestrator | **closed** | tag=RECONCILED => no longer an open blocker |
| 7 | RESOLVED | ~14:07 | **closed** | tag=RESOLVED => no longer an open blocker |
| 8 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (cannot reach White:8099) with no agent-actionable step |
| 9 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (no browser binary) with no agent-actionable step |
| 10 | NEEDS-HUMAN |  | **automatable** | agent-actionable unblock step present (overrides NEEDS-HUMAN tag) |
| 11 | NEEDS-HUMAN |  | **automatable** | agent-actionable unblock step present (overrides NEEDS-HUMAN tag) |
| 12 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (WinError 10013) with no agent-actionable step |
| 13 | NEEDS-HUMAN |  | **human_required** | tag=NEEDS-HUMAN + env/infra wall (Class not registered) with no agent-actionable step |
| 14 | OPS-NOTE | Archivist | **automatable** | tag=OPS-NOTE: operational/data note with a stated remediation, no hard env wall |
| 15 | OPS-NOTE | Pixel | **automatable** | agent-actionable unblock step present |
| 16 | OPS-NOTE |  | **automatable** | tag=OPS-NOTE: operational/data note with a stated remediation, no hard env wall |
| 17 | OPS-NOTE |  | **automatable** | tag=OPS-NOTE: operational/data note with a stated remediation, no hard env wall |
| 18 | OPS-NOTE | Splice | **automatable** | agent-actionable unblock step present |

## Top-3 automatable (with fix path)

1. **Seat-Unavailability Impact Model v2 (goal #8) AC backtest NOT computable: no per-day reach** -> `make the seat-matrix probe APPEND history instead of overwriting - i.`
2. **#3 Build-Verify-Pin: memory_mirror.py is 0 bytes in sandbox** -> `Probe: pathlib.Path("memory_mirror.py").stat().st_size -> 0. Repeated across multiple passes.`
3. **Verifier goal #2 SLO scheduled task: schtasks COM unavailable + egress block in sandbox** -> `Class: sandbox limitation (COM "Class not registered" for schtasks; WinError 10013 for localhost:8099).`
