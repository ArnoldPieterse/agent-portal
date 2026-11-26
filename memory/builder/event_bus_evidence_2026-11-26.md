# Event Bus Evidence — 2026-11-26

**Goal**: #3 Convergence Event Bus (SSE + replay)
**Status**: REACHED

## Selftest (python memory/builder/event_bus.py --selftest)

```
=== event_bus.py selftest ===
  [PASS] A: Broadcast to 2 subscribers in 0.5ms
  [PASS] B: Replay from cursor=0 returns 3 events, final state correct
  [PASS] B2: Partial replay (cursor=2) returns correct subset
  [PASS] C: 50 writes in 15.3ms; slow buffer bounded at 10/10
  [PASS] C2: All 58 source events persisted (no drops in SSOT)

[ALL PASS] event_bus selftest complete
```

## Live Verify (emit + replay on real path)

```
$ python memory/builder/event_bus.py emit fsm_transition '{"from":"CONVERGING","to":"CONVERGING"}' --source selftest_verify
{"seq": 0, "ts": "2026-11-26T12:15:46...", "type": "fsm_transition", ...}

$ python memory/builder/event_bus.py replay 0
{"seq": 0, ...}  [1 events from cursor 0]
```

## Artifacts
- `memory/builder/event_bus.py` — the bus (append-only JSONL + in-process pub/sub + SSE handler + cursor replay)
- `memory/ops/convergence-events.jsonl` — the SSOT event stream (1 live event emitted)

## Acceptance Criteria Mapping
| Criterion | Evidence |
|-----------|----------|
| Simulated transition broadcast to 2 subscribers within 2s | Selftest A: 0.5ms (well under 2s) |
| New subscriber at cursor=0 replays all events, reaches current state | Selftest B: 3 events replayed, final state CONVERGING confirmed |
| Slow consumer does not drop source writes (bounded backpressure) | Selftest C: 50 writes in 15.3ms; buffer bounded at 10/10; all 58 on disk (C2) |