# Post-Mortem — oom_recovery (test_agent)

- **Report ID:** pm-20261123-002
- **Generated:** 2026-11-23T14:42:08.718214+00:00
- **Status:** SUCCESS

## 1. What Broke
oom_recovery on agent `test_agent` at 2026-11-22T22:17:58.698011+00:00 — outcome SUCCESS, severity unspecified.

## 2. Root Cause
gpu_memory_exhausted

## 3. Fix Applied
- reason: gpu_memory_exhausted
- before_model: qwen2.5-7b-fp16
- after_model: qwen2.5-7b-int8
- action_taken: kill+reload(qwen2.5-7b-fp16->qwen2.5-7b-int8)
- rollback_available: True
- rollback_action: reload qwen2.5-7b-fp16

## 4. Time-to-Recovery
0 seconds.

## 5. Lessons Learned
- None recorded; review timeline for improvement opportunities.


---

# Post-Mortem — oom_recovery (test_agent)

- **Report ID:** pm-20261123-003
- **Generated:** 2026-11-23T14:42:08.718222+00:00
- **Status:** SUCCESS

## 1. What Broke
oom_recovery on agent `test_agent` at 2026-11-22T23:10:36.112747+00:00 — outcome SUCCESS, severity unspecified.

## 2. Root Cause
gpu_memory_exhausted

## 3. Fix Applied
- reason: gpu_memory_exhausted
- before_model: qwen2.5-7b-fp16
- after_model: qwen2.5-7b-int8
- action_taken: kill+reload(qwen2.5-7b-fp16->qwen2.5-7b-int8)
- rollback_available: True
- rollback_action: reload qwen2.5-7b-fp16

## 4. Time-to-Recovery
0 seconds.

## 5. Lessons Learned
- None recorded; review timeline for improvement opportunities.
