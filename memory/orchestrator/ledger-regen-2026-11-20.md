# Ledger Regeneration - 2026-11-20 (Orchestrator contribution, option c)

**Action:** Regenerated `goal_ledger.json` from live goal files using `python goal_ledger.py --json`.

**Finding:** Old ledger (generated earlier today) was stale/inflated for 3 agents and undercounted for 4:
| Agent | Old | New | Delta |
|---|---|---|---|
| orchestrator | 6/10 | 8/10 | +2 |
| researcher | 10/10 | 7/10 | -3 (was inflated) |
| builder | 5/10 | 8/10 | +3 |
| archivist | 4/10 | 4/10 | 0 |
| scribe | 0/10 | 3/10 | +3 |
| verifier | 10/10 | 8/10 | -2 (was inflated) |
| designer | 3/10 | 0/10 | -3 (was inflated) |
| mechanic | 2/10 | 8/10 | +6 |

**Fleet total:** 40/80 (50%) -> 46/80 (58%)

**Root cause of inflation:** Old ledger was likely generated when goal files had more `(verified:` markers that were subsequently removed or the file was manually edited. The evidence-gated parser only counts goals with an explicit `(verified:` or `— recorded` marker on the line.

**Artifacts:**
- `goal_ledger.json` (updated, 46/80)
- `goal_ledger.json.bak-20261120` (backup of old stale ledger)

**Impact:** Fleet dashboard will now show accurate progress. Agents previously shown at 100% (researcher, verifier) are correctly shown with open goals, which should re-trigger their auto-loop prompts for those specific items.
