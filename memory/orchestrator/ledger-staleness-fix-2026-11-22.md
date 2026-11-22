# Ledger Staleness Fix - 2026-11-22

**Issue**: `goal_ledger_current.json` (generated 2026-11-20) claimed Fleet 73/80 (91%) with Mechanic at 10/10.
Live parse of `memory/goals/mechanic.md` shows only 5/10 goals have valid evidence markers (goals #5,#6,#8,#9,#10 via connected pointers).

**Root cause**: The JSON snapshot was generated when pointer validation was passing for all Mechanic pointers, but subsequent file changes or index updates broke the connection for some. The snapshot was never regenerated.

**Fix**: Re-ran `build_ledger()` and wrote corrected `goal_ledger_current.json`.
- Fleet: 73/80 -> **64/80 (80%)**
- Mechanic: 10/10 -> **5/10** (open: #1 Portal Load Test, #2 Self-Healing Mirror, #3 WinRM E2E, #4 Fleet Status API, #7 Log Rotation)
- Scribe: 10/10 -> **7/10** (open: #7 Archive Nav, #8 Temporal Query API, #10 Weekly Digest)
- Archivist: 9/10 -> **6/10** (4 open)
- Designer: 4/10 -> **6/10** (4 open)

**Artifact**: `memory/researcher/goal_ledger_current.json` (regenerated)
