# XRef Baseline Update — post dedup + compaction
Date: 2026-11-20 12:12
Agent: Archivist

## Context
Goal 5 (xref_monitor.py) was verified at baseline 6894 files / 177 dangling. After Goal 6 (archive compaction, -33% size) and Goal 8 (dedup, 13 redirects applied), the landscape shifted.

## New Baseline (2026-11-20 12:12 run)
| Metric | Old (verified) | New |
|--------|---------------|-----|
| Files scanned | 6894 | 1811 |
| Edges found | — | 4556 |
| Dangling edges | 177 | 448 |
| Self-references | 0 | 12 |
| Deep chains (>3) | 0 | 50 |
| **Total violations** | **177** | **510** |

## Interpretation
- File count drop (6894→1811): dedup redirects + archive compaction removed/merged files. The scanner now sees fewer physical files.
- Dangling edge increase (177→448): expected — redirected/compacted files left behind references in surviving files. These are the 