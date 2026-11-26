# OOM Recovery Loop - Runbook

**Status**: ACTIVE (simulated 2026-11-26)
**Script**: `memory/mechanic/oom-recovery-loop.py`
**MTTR Target**: <60s
**Evidence**: `memory/mechanic/oom-recovery-evidence.jsonl`

## What Broke / What Fixed It
OOM on a seat's GPU kills the model process, VRAM is held by zombie allocations,
and the seat goes unreachable. The recovery loop detects the missing model via
Studio API, unloads it (frees VRAM), finds a backup host with capacity, loads
the model there, and updates agents.json binding - all without human touch.

## Detection
- Polls `/api/inference/loaded-models` every 10s (watch mode)
- Compares against expected models per HOST_MODELS config
- Triggers on: model present in config but absent from loaded list

## Recovery Sequence (~18-24s typical)
1. **Detect** (0ms) - model gone from expected GPU
2. **Unload** (2-3s) - POST /api/inference/unload to victim host
3. **Find backup** (1-2s) - probe other hosts for capacity
4. **Load on backup** (15-19s) - POST /api/inference/load to backup host
5. **Update binding** (~50ms) - write agents.json with new host_binding

## Operations
```bash
# Run simulation (3 events, verifies <60s)
python memory/mechanic/oom-recovery-loop.py --simulate

# Start continuous monitoring
python memory/mechanic/oom-recovery-loop.py --watch

# Manual trigger for a specific host
python memory/mechanic/oom-recovery-loop.py --recover white
```

## Verification (2026-11-26)
- 3 simulated OOM events: all recovered <60s (max 24.1s, mean 21.1s)
- Zero human intervention required
- Seat restored to original model+quant on backup host
- Evidence: oom-recovery-evidence.jsonl (8 entries)