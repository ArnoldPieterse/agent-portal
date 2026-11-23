# Forecast: Archivist Cycle-12 Open Goals (6 remaining)

Generated: 2026-11-24 by Orchestrator
Basis: goal complexity, dependencies on existing artifacts, and fleet throughput (~28.9 goals/h historical).

## Dependency Map
```
#4 conflict_resolver  <- provenance_ledger.py (DONE #1), kb_index.json
#5 kb_feedback        <- decision-log.jsonl (Builder playbook_runner output), Researcher loop-closure data
#6 access_heatmap     <- tool-read logs, decision-log citations
#8 kb_sentinel        <- knowledge-index.json, snapshot diff (cycle-2 infra)
#9 summary_ladder     <- all existing leaves; no hard dependency on #4-#8
#10 kb_version        <- knowledge-index.json; independent of others
```

## Predicted Completion Order & Timing
| Goal | Est. Effort | ETA | Risk |
|------|------------|-----|------|
| #6 Access Heatmap | Low (instrument + aggregate) | 1 cycle | Low - data already exists in decision-log.jsonl |
| #9 Summary Ladder | Medium (3-tier generation per lane) | 1-2 cycles | Medium - needs quality gate on abstracts |
| #4 Conflict Resolver | Medium (pairwise comparison + report) | 2 cycles | Medium - false-positive rate tuning |
| #8 KB Sentinel | Low-Medium (scheduled check + alert) | 1 cycle | Low - reuses snapshot diff infra |
| #5 KB Feedback Loop | High (traces decisions back to knowledge) | 2-3 cycles | High - depends on Researcher loop-closure data maturing |
| #10 KB Versioning | Medium (git-backed + rollback cmd) | 1 cycle | Low - straightforward git ops |

## Critical Path
#5 is the longest pole. It needs Researcher's loop-closure classifications to be mature. 
If Researcher's remediation_bus (DONE) starts producing REVERTED decisions, #5 unblocks immediately.
Recommend Archivist tackle in order: 6 -> 8 -> 9 -> 10 -> 4 -> 5

## Fleet Impact
- #6 + #8 together enable the Cockpit "Knowledge Health" panel (currently stubbed)
- #9 reduces token burn for small-context models reading KB (direct cost saving)
- #10 provides safety net for all other KB changes (should precede aggressive refactors)

## Confidence: MEDIUM
- Throughput estimate based on 7-day window; actual pace may vary with model availability.
- #5's dependency on Researcher output is the main uncertainty (could be 1 or 4 cycles).
