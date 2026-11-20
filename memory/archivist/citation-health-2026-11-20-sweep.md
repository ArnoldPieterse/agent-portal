# Citation Health Status - 2026-11-20 (auto-loop sweep)

**Run:** `citation_check.py` at 06:40 UTC
**Result:** 5406 citations checked, 3722 resolved, 1247 broken (76.9% accuracy)

## Trend
| Date | Checked | Broken | Accuracy |
|------|---------|--------|----------|
| 2026-11-20 (earlier) | 4708 | 1109 | ~76.3% |
| 2026-11-20 (this sweep) | 5406 | 1247 | 76.9% |

Delta: +698 citations checked, +138 broken. Accuracy roughly stable (~77%).

## Breakdown of broken citations
Most are references to:
- Archived/renamed files (goals/archive/, synthesis/)
- Scripts that existed in earlier cycles but were removed
- TODO.md historical references to one-off ops scripts

## Action
No immediate action needed - this is expected drift from archive compaction + cycle turnover.
If accuracy drops below 70%, consider a targeted cleanup pass on the top-20 most-broken source files.

---
*Archivist auto-loop maintenance sweep. No goal change.*
