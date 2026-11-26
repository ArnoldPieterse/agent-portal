# Model Load Failure Runbook

## Trigger
Model fails to load on seat (timeout, missing file, VRAM insufficient).

## Steps
1. Check model-load.jsonl for the failure entry (reason field)
2. If missing file: verify mirror sync completed; re-sync if needed
3. If VRAM insufficient: downgrade quant (fp16->int8) or offload to backup seat
4. Retry load with adjusted params
5. If 3 retries fail: mark seat degraded, route goals to backup

## SLA
Load retry < 30s per attempt; max 3 attempts before escalation
