# Seat Failover Drill - 2026-11-26

Mode: simulation (3 drills)

## Drill 1: white -> red
- Model: Qwen3.8-27B-Q8_0
- Agents affected: orchestrator, researcher, scribe
- Total time: 40.1s (SLA <120s: PASS)
- Goal loss: 0

## Drill 2: red -> white
- Model: Qwen3.8-27B-GGUF
- Agents affected: mechanic, archivist
- Total time: 36.1s (SLA <120s: PASS)
- Goal loss: 0

## Drill 3: black -> white
- Model: Qwen3.8-27B-Q8_0
- Agents affected: verifier, designer, forge
- Total time: 40.1s (SLA <120s: PASS)
- Goal loss: 0

## Verdict: ALL PASS