# Self-Correction Tracker — Evidence (2026-11-25)
## Verification
- Script: `memory/researcher/self_correction.py` (standalone, exit 0)
- Data: 336 correction events from archive keyword patterns across 9 agents
- Per-agent table: 8 agents with n>=5 (all except 'unknown' which has n=3)
- Trend: IMPROVING - correction rate dropped from 45.9% (early period) to 21.9% (late period)
- CI: 95% early [40.4%, 51.4%], late [19.2%, 24.6%] - non-overlapping = significant improvement
- Success rate range: 52% (mechanic/orchestrator) to 88% (builder)
- Latency proxy: ~0-1.5 passes (same-pass detection + date estimation)

## AC Verification
| AC | Status | Evidence |
|---|---|---|
| >=5 correction events | PASS | n=336 |
| Per-agent latency table | PASS | 8 agents with >=5 events, each has success rate + avg latency |
| Trend direction with confidence | PASS | "improving" with 95% CI (non-overlapping intervals) |

## Caveats
- Latency is a PROXY (not true pass-level timing; would need per-pass autoloop timestamps)
- "Resolved" detection uses keyword matching in forward context - may miss implicit resolutions
- Correction types dominated by 'stale' claims (251/336 = 75%)

Confidence: HIGH on counts and trend direction; MEDIUM on latency precision
