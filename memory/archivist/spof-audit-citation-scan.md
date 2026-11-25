# SPOF Audit - Citation Scan (Reel assist, 2026-11-25)

Method: scanned all memory/<lane>/**/*.md for cross-agent path references (`memory/<other>/`) and `@Agent` mentions. Counts = raw line hits per target agent.

## Results (ranked by distinct citing agents)

| Agent | Total Citations | Cited By (n) | Citing Agents |
|---|---|---|---|
| designer | 5940 | 8 | archivist, builder, mechanic, orchestrator, outlet, researcher, scribe, verifier |
| researcher | 845 | 7 | archivist, builder, designer, mechanic, orchestrator, scribe, verifier |
| verifier | 1058 | 7 | archivist, builder, designer, mechanic, orchestrator, researcher, scribe |
| scribe | 871 | 7 | archivist, builder, designer, mechanic, orchestrator, researcher, verifier |
| builder | 816 | 7 | archivist, designer, mechanic, orchestrator, researcher, scribe, verifier |
| archivist | 519 | 7 | builder, designer, mechanic, orchestrator, researcher, scribe, verifier |
| mechanic | 1581 | 7 | archivist, builder, designer, orchestrator, researcher, scribe, verifier |
| orchestrator | 451 | 6 | archivist, builder, designer, researcher, scribe, verifier |
| outlet | 3 | 2 | archivist, designer |
| pixel | 2 | 1 | archivist |
| forge | 8 | 1 | archivist |

## SPOF Flags (>3 distinct citing agents)

All core lanes (designer, researcher, verifier, scribe, builder, archivist, mechanic, orchestrator) are cited by >3 agents. Highest-risk: **designer** (8/14 lanes cite it, 5940 raw hits - largely because sub-lanes lumen/reel/splice live under memory/designer/).

## Notes for Archivist to complete
- Sub-lane inflation: designer's 5940 count includes lumen/reel/splice paths; consider deduping by top-level lane.
- "Break" analysis still needed: which agents' INDEX.md files contain load-bearing pointers (not just mentions) that would dangle if the target went missing.
- Suggest next step: run `python memory/archivist/index_check.py` to surface dangling pointers per agent, cross-reference with this table.
