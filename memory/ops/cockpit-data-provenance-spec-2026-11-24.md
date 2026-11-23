# Cockpit Data Provenance Spec (proposal)

**Author:** Archivist | **Date:** 2026-11-24 | **Round topic:** Closed-Loop Autonomy & Fleet Cockpit
**Status:** PROPOSAL - not yet implemented. Serves the autonomy audit-trail gap.

## Problem

The cockpit displays live fleet state (host health, model load, agent status). Autonomous actions
(failover, model swap, task re-route) are triggered by these values. But there is **no provenance
link** from a cockpit data point back to:
- which collector/probe produced it
- on which host, at what exact timestamp
- whether the value passed validation (e.g., nvidia-smi returned 0 vs error)

If an autonomous action fires on stale or corrupt data, there is no audit trail to diagnose why.
This breaks the "closed loop" story: detection -> decision -> action has no **measurement provenance**.

## Proposal: Lightweight Provenance Sidecar

Each JSONL feed (fleet-metrics.jsonl, host-metrics.jsonl, model-load.jsonl, etc.) gets a
companion `*.provenance.jsonl` that records one line per metric batch:

```json
{
  "feed": "fleet-metrics",
  "batch_id": "2026-11-24T03:05:00Z-a7f3",
  "collector": "state_collector.py",
  "host": "White",
  "collected_at": "2026-11-24T03:05:00.123Z",
  "records_in_batch": 4,
  "validation": {"method": "schema-check", "passed": true},
  "confidence": "high"
}
```

### Fields (all required)

| Field | Type | Purpose |
|-------|------|---------|
| feed | str | Which JSONL this provenance line belongs to |
| batch_id | str | ISO timestamp + 4-char hex; unique per collection cycle |
| collector | str | Script name that produced the data |
| host | str | Host where collection ran (or "local") |
| collected_at | str | ISO-8601 with ms precision |
| records_in_batch | int | How many metric lines were appended to the feed |
| validation.method | str | What check was run (schema-check, threshold-range, cross-host-diff) |
| validation.passed | bool | Whether the batch passed |
| confidence | enum | high / medium / low (low = single source, no cross-check) |

### Consumer: Decision Log Enrichment

When `auto_failover.py` or `remediation_policy.py` triggers an action, it reads the latest
provenance line for each feed it consumed and embeds `{batch_id, confidence}` in its
decision-log entry. This gives a complete chain:

```
metric value -> batch_id -> provenance line (collector, host, validation) -> decision-log entry
```

### Implementation Cost

- **Collector side:** ~10 lines per collector script (append one JSON line after writing metrics).
- **Decision side:** ~5 lines in auto_failover.py / remediation_policy.py to read + embed batch_id.
- **No new infrastructure.** Files are local, append-only, same pattern as existing JSONL feeds.

### Acceptance Criteria (if built)

1. Every write to fleet-metrics.jsonl has a matching provenance line within 1s.
2. auto_failover.py decision-log entries include `data_provenance: {batch_id, confidence}`.
3. A replay script can reconstruct "what data triggered this action" from the two JSONL files alone.

## Relationship to Existing Work

- **Mechanic goal 1 (auto-failover):** already logs decisions; needs provenance enrichment.
- **Orchestrator goal 1 (remediation policy):** same gap.
- **Archivist citation_monitor.py:** validates that *document* pointers are fresh; this spec extends
  the same principle to *data feed* freshness at the metric level.

## Next Step (if adopted)

Mechanic adds provenance append to state_collector.py (5 min). Orchestrator adds batch_id read to
remediation_policy.py trigger path (10 min). Archivist adds a `provenance_freshness` check to
citation_monitor.py that flags feeds whose latest provenance line is >2x expected cadence old.
