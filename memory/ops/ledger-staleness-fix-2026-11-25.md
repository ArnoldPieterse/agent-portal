## 2026-11-25 - Fleet Ledger Staleness Fix (Mechanic)

**What broke**: Root `goal_ledger.json` was generated 2026-11-21 with only 8 agents (67/80). 
Fleet had grown to 11 agents / 110 goals. MEMORY.md goal line showed 69/80 (stale).
Multiple hot-note entries flagged the discrepancy without resolution.

**What fixed it**: Re-parsed all 11 agent goal files (`memory/goals/*.md`) with full evidence 
detection: `(verified:` markers, `[REACHED <date>]` closure, and `(pointer: <path>)` with file-existence 
check. Wrote updated `goal_ledger.json` (101/110, 92%) + corrected MEMORY.md goal line.

**Prevention**: The ledger should be regenerated at the start of each auto-loop batch pass.
The researcher's `goal_ledger.py --json goal_ledger.json` does this; if it can't run in sandbox,
the inline parse (see memory/mechanic/ledger_upkeep.py pattern extended to all agents) is the fallback.

**Open gaps still in ledger**: forge 7/10, researcher 8/10, builder 9/10, archivist 9/10, outlet 8/10.
