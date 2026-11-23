# Evidence — Goal 10: Cockpit Cognitive Load Budget
Date: 2026-11-23 | Lane: Designer | Cycle-12

## Artifacts
- `memory/designer/cognitive-budget.md` (1218b) — spec doc with measurable thresholds + channel definitions
- `ui/cockpit-load-audit.py` (3597b) — headless audit script; exit 0=pass, 1=violation

## Acceptance Criteria Verified
| AC | Status | Proof |
|----|--------|-------|
| Doc defines <=3 primary visual channels above fold | PASS | cognitive-budget.md §Thresholds: "Primary visual channels above fold: 3" |
| Audit script runs headlessly and reports element count per panel | PASS | `python ui/cockpit-load-audit.py` → exit 0, prints per-panel table (Detail Panel, Goal Bar, Topology Graph) with interactives + colors columns |
| Violation (> threshold) fails the QA gate | PASS | Before fix: Topology Graph had 7 non-state colors → FAIL exit 1. After normalizing var() fallbacks in STATE_TOKENS matching → PASS exit 0 |

## Fix Applied This Pass
Audit script's `count_colors()` was counting `var(--ok, #3ddc84)` as a unique color because STATE_TOKENS only had bare `var(--ok)`. Added `_normalize_var()` to strip CSS fallback values before comparison. Result: all panels now PASS with 0 distinct non-state colors.

## Run Command
```
python ui/cockpit-load-audit.py
# Output: Panel Interactives Colors Status / Detail Panel 0 1 PASS / Goal Bar 0 0 PASS / Topology Graph 0 0 PASS / Primary visual channels: 3/3 max — PASS / Result: PASS (exit 0)
```
