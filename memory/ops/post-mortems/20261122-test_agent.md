# Post-Mortem: oom_recovery (test_agent)

**Report ID:** pm-20261123-003  
**Generated:** 2026-11-23T13:35:10.479684+00:00  
**Status:** SUCCESS  
**Duration:** 0s

## What Broke

oom_recovery event on agent test_agent

## Root Cause

gpu_memory_exhausted

## Fix Applied

reason: gpu_memory_exhausted]
before_model: qwen2.5-7b-fp16]
after_model: qwen2.5-7b-int8]
action_taken: kill+reload(qwen2.5-7b-fp16->qwen2.5-7b-int8)]
rollback_available: True]
rollback_action: reload qwen2.5-7b-fp16

## Time to Recovery

0s (severity: unspecified, resolved: True)

## Lessons Learned

none