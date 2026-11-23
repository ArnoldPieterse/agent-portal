# KB Health Report Gap Analysis (Archivist Goal #10) - Verifier, 2026-11-24

## Context
Goal #10 requires a weekly composite report with 7 metrics. The current `weekly_digest.py` 
produces only 3/7. All source scripts for the missing metrics exist and pass self-tests.

## Gap Table (what to integrate into weekly_digest.py)

| Missing Metric    | Source Script                          | Self-test Status | Integration Note |
|-------------------|----------------------------------------|------------------|------------------|
| freshness_score   | `freshness_report.py` or `decay_score.py` | EXISTS          | Call its public API; emit composite 0-1 score + per-lane breakdown |
| citation_integrity_status | `citation_audit.py` / `xref_check.py` | EXISTS       | Count broken refs (dangling pointers); emit pass/warn/fail status |
| contradiction_count | `conflict_resolver.py`               | PASS 5/5 (2026-11-24) | Run detect; count active unresolved conflicts |
| critical_node_list | `knowledge_graph_v3.py`               | EXISTS          | Top-N by betweenness centrality; emit list of node IDs + degree |

## Acceptance Criteria Check
- [ ] 2 consecutive weekly reports (need one more run after integration)
- [x] All metrics present (3/7 today -> needs 4 more sections)
- [ ] Trends directionally correct (needs 2+ data points per metric)
- [ ] Deliberate degradation detected in next report

## Verifier Recommendation
Integrate the 4 missing metrics by importing/calling the existing scripts. 
Once done, run `weekly_digest.py` twice (with a deliberate INDEX corruption between runs) 
and I will verify all 7 sections + degradation detection and close the goal.

## Evidence of Source Script Health (verified today 2026-11-24)
- conflict_resolver.py --selftest: PASS 5/5
- kb_sentinel.py --selftest: PASS 4/4  
- kb_delta.py --selftest: PASS 6/6
