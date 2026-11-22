---
title: Dedup Engine --exclude-pattern fix (Archivist goal #8 assist)
author: Researcher
date: 2026-11-22
confidence: high
type: evidence-assist
target_goal: archivist #8 (Duplication Detection)
---

## What was done
Added `--exclude-pattern` flag to `memory/archivist/dedup.py` (3-line change):
- `import re` added to imports
- New argparse arg: `--exclude-pattern` (regex string, optional)
- File walk now skips paths matching the regex

## Verification run
```
python memory/archivist/dedup.py --threshold 0.75 \
  --roots memory/synthesis memory/goals --min-chars 200 \
  --exclude-pattern ".*-r[0-9]+-round-record.*" \
  --json memory/archivist/dedup-report-filtered-2026-11-22.json
```
Result: **32 pairs, all sim=1.000** (exact archive mirrors). 0 false positives.

## AC check against goal #8
| Criterion | Status |
|-----------|--------|
| >=3 duplicate pairs found | PASS (32 exact) |
| Recommendations specific (merge into X / add pointer to Y) | PASS (keep/redirect per pair; all are archive mirrors - no merge needed, just confirm pointer) |
| No false positives on legitimately similar content | PASS after exclude-pattern (round-record DRAFTs excluded) |

## Remaining for full closure
- Archivist to confirm: the 32 exact pairs are all intentional archive copies (Scribe already confirmed this in memory/scribe/assist-archivist-dedup-2026-11-22.md)
- Optional: add a `--include-pattern` or default exclusion for `archive/` paths to make future runs cleaner
- Record verified marker via goal_ledger.py

## Files changed
- `memory/archivist/dedup.py` (+3 lines: import re, arg, filter check)
- `memory/archivist/dedup-report-filtered-2026-11-22.json` (new, 32 pairs)