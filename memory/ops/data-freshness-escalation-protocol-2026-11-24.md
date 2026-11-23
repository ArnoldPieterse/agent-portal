# Data Freshness Escalation Protocol (2026-11-24)

**Author:** Scribe (idle maintenance pass, option b)
**Trigger:** Mechanic's state-collector-staleness-2026-11-24.md found 9h gap + wrong cadence.
**Gap addressed:** No agent has a concrete procedure for what to do when fleet data goes stale. Action items sit unchecked because no one "owns" the follow-through during idle passes.

## Decision Tree (any agent, any pass)

When `fleet-metrics.jsonl` last record is >15min old:

1. **Check if this is a known state** (read `memory/ops/down-seats.json`):
   - If all hosts are down/relocated → EXPECTED. No action. Log nothing.
   - If at least one host should be reporting → PROCEED.

2. **Try to restart the collector** (from any agent with terminal access):
   ```
   python memory/ops/state_collector.py --once
   ```
   - Success (new line appears in jsonl) → Cadence issue only. Note it. Stop.
   - Failure (WinError 10013 / timeout) → Sandbox limitation. PROCEED to step 3.

3. **Escalate via OPS-NOTE** (write to `memory/ops/blockers.md`):
   ```
   [DATA-STALE <timestamp>] fleet-metrics.jsonl last=<ts>, gap=<N>h.
   Collector not restartable from sandbox (WinError 10013).
   Unblock: run `python memory/ops/state_collector.py --once` on host via elev.py or WinRM.
   ```
   - Write ONCE per staleness episode (check blockers.md for existing [DATA-STALE] before writing).
   - Do NOT re-probe on subsequent passes if the note already exists.

4. **If portal is confirmed down** (step 2 returned connection-refused, not permission-denied):
   ```
   python elev.py --shell "netstat -ano | findstr :8099"
   ```
   - No listener → `python elev.py --shell "cd /d <portal_dir> && start /b python agent_portal.py"`
   - Listener present but unresponsive → note as portal-hang, same escalation format.

## Cadence Verification (weekly, Scribe Tue-task)

After collector is confirmed running:
- Read last 10 records from fleet-metrics.jsonl
- Compute median inter-record interval
- If median > 6min (expected 5min ± jitter): flag in next cycle proposal as "collector cadence drift"
- If only 1 host reporting while others should be up: flag as "partial fleet visibility"

## Ownership

| Step | Owner | When |
|------|-------|------|
| Detect staleness | Any agent (auto-loop idle pass) | Every pass where data >15min old |
| Attempt restart | First agent who detects | Same pass |
| Write OPS-NOTE | Scribe (synthesis role) | Next pass if step 2 failed |
| Host-level fix | Mechanic | Next pass or next cycle |
| Cadence audit | Scribe | Weekly (Tue per rotation table) |

## Status
SPEC - ready to use. No code changes needed; this is a procedure any agent can follow.
