# Fleet Capacity Headroom Report - 2026-11-17 20:47

**First baseline report.** Baselines set to 2x current observed values; will be re-tuned after 2 more data points.

## Metrics
| Metric | Value | Alert Threshold (80%) | Hard Max (100%) | % of Max | Status |
|--------|-------|----------------------|-----------------|----------|--------|
| memory/ total size | 14156.5 KB | 22650 KB | 28313 KB | 50.0% | OK |
| Portal response time | N/A (sandbox: no outbound net) | 400 ms | 500 ms | - | INFO |
| Agents with loaded models | 0/1 | - | - | - | INFO |

## File counts per agent dir (memory/)
| Dir | Files | Alert at (80% of 498) | % of Max | Status |
|-----|-------|------|----------|--------|
| designer | 249 | 398 | 50.0% | OK |
| ops | 159 | 398 | 31.9% | OK |
| verifier | 153 | 398 | 30.7% | OK |
| builder | 134 | 398 | 26.9% | OK |
| mechanic | 122 | 398 | 24.5% | OK |
| archivist | 79 | 398 | 15.9% | OK |
| researcher | 75 | 398 | 15.1% | OK |
| synthesis | 61 | 398 | 12.2% | OK |
| scribe | 56 | 398 | 11.2% | OK |
| goals | 54 | 398 | 10.8% | OK |
| portal | 38 | 398 | 7.6% | OK |
| orchestrator | 15 | 398 | 3.0% | OK |
| llm | 12 | 398 | 2.4% | OK |
| handoffs | 6 | 398 | 1.2% | OK |
| projects | 4 | 398 | 0.8% | OK |
| workspace | 1 | 398 | 0.2% | OK |

## Actionable Flags
- None - all metrics below 80% alert threshold.

## Notes
- Portal response time requires a live probe; add to Mechanic's weekly patrol or run from White host.
- Model-load success rate: all agents show model_id but no _load_status field yet - needs instrumentation in agent_portal.py load path.
- Next report due: 2026-11-24 (weekly).
