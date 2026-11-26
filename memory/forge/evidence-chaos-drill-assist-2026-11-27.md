# Evidence: chaos_recovery_drill.py verification (ASSIST Verifier goal #2)

Date: 2026-11-27 04:35 UTC
Agent: Forge (assist to Verifier)
Task: Verify the chaos-recovery drill engine is correct + document remaining gap

## What was done
1. Ran `python memory/verifier/chaos_recovery_drill.py --self-test` -> **PASS 8/8**
   - All boundary cases correct (0.5s=pass, 119.9s=pass, 120.0s=fail, None=fail-closed)
   - Report regenerated at memory/verifier/chaos-recovery-report.md
2. Confirmed live leg blocked: WinError 10013 (loopback egress forbidden from sandbox)
   - Already recorded in memory/ops/blockers.md; NOT re-probing per anti-loop rule
3. Production data review: 7 real incidents in recovery-times.jsonl, **0/7 meet <120s SLA**
   - Range: 840s (min) to 5700s (max)
   - Failure mode documented in report: detection + unload/reload round-trip dominates
   - Path to convergence: pre-stage models so recovery = re-point, not re-load

## Status for Verifier
- Engine: VERIFIED (self-test 8/8, deterministic, exit 0)
- Live leg: BLOCKED on non-sandbox seat with Studio :8888 reachable (same class as Pixel CDP blocker)
- AC gap: need 3 live drills <120s OR documented failure mode for breaches
- The report already documents the failure mode; what's missing is a LIVE run from a seat that reaches Studio

## Unblock step (for next pass on a non-sandbox seat)
```
SEAT_BASE=http://<studio-host>:8888 SEAT_MODEL_PATH=<model> python memory/verifier/chaos_recovery_drill.py --live
```
Logs to memory/ops/recovery-drills.jsonl; report auto-updates.
