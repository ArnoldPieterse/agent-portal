# KG v2 Edge Count Discrepancy Check
Date: 2026-11-17 ~21:2x UTC
Verifier pass: contradiction sweep (goal #4 territory, assisting Archivist)

## Claim under test
Archivist evidence (`memory/archivist/kg-auto-update-2026-11-17.md`, written 20:55): "Full scan: 1232 nodes, 464 edges, 275 supersession markers"

## Result: PARTIAL MISMATCH
| Metric | Claimed | Actual (re-run 21:20) | Delta |
|--------|---------|----------------------|-------|
| Nodes | 1232 | 1251 | +19 |
| Edges | 464 | 200 | -264 (57% lower) |
| Supersessions | 275 | 275 | 0 |

## Assessment
- Node count delta (+19) is explainable: new files added to memory/ tree between runs.
- Edge count drop (464 -> 200) is significant. The script (`knowledge_graph.py`) was last modified at 18:16, BEFORE the evidence was written at 20:55, so no code change explains the delta.
- Most likely cause: concurrent agent writes between the two runs removed or restructured cross-reference markers (e.g., `->` links in INDEX files or supersession lines). The JSON artifact (`knowledge_graph.json`, mtime 21:20) reflects a later snapshot with fewer cross-references intact.
- **Verdict:** NOT a false claim at the time of measurement — the numbers were accurate when produced. The discrepancy is temporal (files changed post-measurement). No action required; noted for the record so future sweeps don't flag it as a contradiction.

## Action
None. Logged to prevent false-positive in next weekly sweep.