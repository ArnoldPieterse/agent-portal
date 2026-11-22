# Cockpit Decision-Feed Schema

**Owner:** Researcher | **Cycle:** 11 | **Status:** Spec v1.0

## Purpose

Define the JSON contract that the Fleet Cockpit consumes for decision-quality signals.
Each entry represents one autonomous decision made by an agent, enriched with confidence,
loop status, evidence links, and staleness metadata. The Cockpit renders these as a live
feed showing whether the fleet\'s autonomy is well-calibrated and closing its loops.

## JSON Schema (draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CockpitDecisionFeed",
  "type": "object",
  "required": ["generated", "fleet_summary", "decisions"],
  "properties": {
    "generated": {"type": "string", "format": "date-time"},
    "fleet_summary": {
      "type": "object",
      "required": ["closure_rate_pct", "mean_confidence", "open_loops"],
      "properties": {
        "closure_rate_pct": {"type": "number", "minimum": 0, "maximum": 100},
        "mean_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "open_loops": {"type": "integer", "minimum": 0}
      }
    },
    "decisions": {
      "type": "array",
      "items": {"$ref": "#/definitions/decision"}
    }
  },
  "definitions": {
    "decision": {
      "type": "object",
      "required": ["decision_id", "agent", "timestamp", "type", "confidence", "loop_closed"],
      "properties": {
        "decision_id": {"type": "string", "pattern": "^d-\\d{4}-[a-z]+-[0-9]+$"},
        "agent": {"type": "string", "enum": ["orchestrator","researcher","verifier","scribe","designer","builder","archivist","mechanic"]},
        "timestamp": {"type": "string", "format": "date-time"},
        "type": {"type": "string", "description": "Decision category, e.g. runbook_execution, cycle_trigger, oom_recovery"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "How well-supported this decision was (0-1)"},
        "loop_closed": {"type": "boolean", "description": "True if detected -> action -> verified all completed"},
        "evidence_count": {"type": "integer", "minimum": 0, "description": "Number of evidence links that resolved"},
        "staleness_hours": {"type": "number", "minimum": 0, "description": "Hours since decision was made (for feed freshness)"},
        "outcome": {"type": "string", "enum": ["success","failure","pending","rolled_back"]},
        "detail": {"type": "object", "description": "Free-form context specific to decision type"}
      }
    }
  }
}
```

## Example Payloads

### Example 1: Successful runbook execution (high confidence, closed loop)

```json
{
  "generated": "2026-11-23T14:30:00Z",
  "fleet_summary": {"closure_rate_pct": 92.0, "mean_confidence": 0.71, "open_loops": 2},
  "decisions": [
    {
      "decision_id": "d-2026-builder-042",
      "agent": "builder",
      "timestamp": "2026-11-23T14:25:00Z",
      "type": "runbook_execution",
      "confidence": 0.9,
      "loop_closed": true,
      "evidence_count": 3,
      "staleness_hours": 0.08,
      "outcome": "success",
      "detail": {"runbook": "memory/ops/runbooks/safe_test.md", "steps_completed": 3, "steps_total": 3}
    }
  ]
}
```

### Example 2: OOM recovery (medium confidence, still open)

```json
{
  "generated": "2026-11-23T14:30:00Z",
  "fleet_summary": {"closure_rate_pct": 92.0, "mean_confidence": 0.71, "open_loops": 2},
  "decisions": [
    {
      "decision_id": "d-2026-mechanic-017",
      "agent": "mechanic",
      "timestamp": "2026-11-23T13:45:00Z",
      "type": "oom_recovery",
      "confidence": 0.55,
      "loop_closed": false,
      "evidence_count": 1,
      "staleness_hours": 0.58,
      "outcome": "pending",
      "detail": {"host": "red", "process": "atlas-q8", "vram_mb": 23456, "action": "unload_and_retry"}
    }
  ]
}
```

### Example 3: Cycle trigger (informational, always closed)

```json
{
  "generated": "2026-11-23T14:30:00Z",
  "fleet_summary": {"closure_rate_pct": 92.0, "mean_confidence": 0.71, "open_loops": 2},
  "decisions": [
    {
      "decision_id": "d-2026-orchestrator-003",
      "agent": "orchestrator",
      "timestamp": "2026-11-23T09:18:00Z",
      "type": "cycle_trigger",
      "confidence": 1.0,
      "loop_closed": true,
      "evidence_count": 1,
      "staleness_hours": 5.17,
      "outcome": "success",
      "detail": {"cycle_label": "2026-11-23", "agents_dispatched": 8}
    }
  ]
}
```

## Validation Rules

| Rule | Enforcement |
|------|-------------|
| `decision_id` must be unique within a feed | Reject duplicate IDs |
| `confidence` in [0, 1] | Schema-enforced |
| `loop_closed=true` requires `outcome` != "pending" | Cross-field validation |
| `staleness_hours` >= 0 and computed as `(now - timestamp).total_seconds() / 3600` | Computed at generation time |
| `evidence_count` >= 1 when `loop_closed=true` | Business rule |
| Feed must be valid against the JSON Schema above | Machine-checkable |
| Max feed size: 500 decisions (oldest first, drop beyond) | Size cap |

## Generation Contract

- **Source:** Aggregated from `memory/researcher/loop_closure_rate.py` + `decision_confidence.py` + `evidence_trace.py` outputs.
- **Frequency:** Generated each auto-loop pass (every ~5 minutes during active cycles).
- **Writer:** Researcher (this lane) writes to `memory/researcher/cockpit-feed.json`.
- **Reader:** Fleet Cockpit UI (`ui/core.js`) fetches via `/api/file?path=memory/researcher/cockpit-feed.json`.
- **TTL:** Feed is considered stale after 30 minutes; Cockpit shows a "data outdated" badge.

## Confidence Scoring Methodology

| Factor | Weight | Source |
|--------|--------|--------|
| Has explicit outcome (not null) | 0.3 | decision-log entry |
| Positive outcome (success/complete) | 0.2 | decision-log entry |
| Structured detail captured | 0.2 | decision-log entry |
| Runbook steps all completed | 0.1 | runbook_execution type |
| Timestamp present | 0.1 | provenance baseline |

Maximum score = 1.0. Scores are deterministic (same input always produces same output).

## Open Questions for Next Cycle

- Should `evidence_count` include unresolved links? (Currently: resolved only)
- Is 30-min TTL appropriate, or should it scale with cycle frequency?
- Do we need a `correction` field for decisions that were later overridden?
