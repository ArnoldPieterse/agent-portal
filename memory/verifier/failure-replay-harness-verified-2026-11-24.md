# Failure Replay Harness — VERIFIED 2026-11-24

## Summary
Goal #6 (Cycle-14): **Failure Replay Harness** — replay historical failure scenarios from decision-log; verify applied fixes prevent recurrence.

## Verification
- `failure_replay.py --self-test`: **7 PASS / 0 FAIL** from BOTH repo root and memory/verifier (CWD-independent, all paths __file__-anchored)
- Ran twice consecutively (idempotent, no state leaks between runs)
- T1-T6: Built-in fault types (file_corruption, stale_feed, agent_unresponsive, config_drift) + edge cases (unknown type graceful fail, zero-threshold detection, no-drift non-detection, single-ID replay)
- T7: Decision-log integration — reads decision-log.jsonl (9 entries), maps degradation_type → fault_type, replays all 9 scenarios, all pass

## Key Design
- `--from-decision-log` mode extracts replayable scenarios from real historical entries (R001-R005 + variants)
- TYPE_MAP: model_oom→config_drift, vram_pressure→stale_feed, host_unreachable→agent_unresponsive, disk_space→file_corruption
- Each replay: simulate fault → detect → apply fix → verify recurrence prevented
- Graceful empty-replay when no scenarios found (no crash)

## Artifact
memory/verifier/failure_replay.py (13573 bytes)
