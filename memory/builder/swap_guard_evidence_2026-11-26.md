# Swap Guard Evidence — 2026-11-26

**Goal**: #9 Model-Swap Convergence Guard
**Status**: REACHED

## Selftest (python memory/builder/swap_guard.py --selftest)

```
=== swap_guard.py selftest ===
  [PASS] A: In-flight goals block swap (2 goals detected)
  [PASS] B1: Clean seat (all goals reached) passes in-flight check
  [PASS] B2: Alias resolution passes (Alias 'model-b' resolves (known in fleet))
  [PASS] B3: Unknown alias correctly blocked
  [PASS] C: Guard log mechanism works (3 entries)
  [PASS] B3: Before-snapshot has valid sha for Forge consistency diff

[ALL PASS] swap_guard selftest complete
```

## Live Run (python memory/builder/swap_guard.py builder atlas-q8 --dry-run)

Blocked correctly: Builder has 3 in-flight goals (#3 Event Bus, #9 this guard, #10 Observability Bundle).
Exit code 1, reason logged to swap-guard.jsonl.

## Artifacts
- `memory/builder/swap_guard.py` — the guard script (4 pre-flight checks: in-flight goals, VRAM, alias resolution, FSM state)
- `memory/builder/swap-guard.jsonl` — decision log (3 entries from selftest + live run)
- `memory/builder/swap-snapshots/clean_agent_before_*.json` — before-snapshot with agents_json_sha, fsm_state=CONVERGING
- `memory/builder/swap-snapshots/clean_agent_after_*.json` — after-snapshot (same schema) for Forge consistency diff

## Acceptance Criteria Mapping
| Criterion | Evidence |
|-----------|----------|
| Swap on seat with in-flight goal BLOCKED with reason | Selftest A + live run (3 goals listed, exit 1) |
| Clean swap PROCEEDS + emits before/after snapshots for Forge | Selftest B1/B2/B3 + snapshot files have agents_json_sha (16-char hex) + fsm_state |
| Guard logs to swap-guard.jsonl | Selftest C: 3 entries with ts, agent, decision, reason fields |