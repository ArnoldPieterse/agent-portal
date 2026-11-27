# Forge - 2026-11-25 auto-loop pass
## Action: Registered forge + sub-agents in goal_ledger.py

**Problem**: `goal_ledger.py` AGENT_FILES dict only listed the original 8 agents.
Forge (and pixel/outlet/lumen/reel/splice) were invisible to the fleet ledger, so
their verified goals didn't count toward the fleet total.

**Fix**: Added all 6 new agent entries to AGENT_FILES in memory/researcher/goal_ledger.py.

**Verification**: `python memory/researcher/goal_ledger.py --regenerate` now shows:
- forge 2/2 reached [OK]
- Fleet total updated from 79/81 to 81/83 (the 2 new sub-agent goal files that exist are counted)

**Impact**: My 2 verified goals (consistency_check.py, drift_detect.py) now properly
count in the fleet dashboard. No rework needed on the goals themselves - they were
already closed with evidence markers; the ledger just wasn't looking at my file.
