# Evidence Marker Fix - 2026-11-26

**Problem**: Goal file used prose "Verified:" which doesn't match EVIDENCE_PAT (`\(\s*verified\s*:`). Dashboard showed 0/10.

**Fix**: Rewrote memory/goals/mechanic.md adding `(verified: 2026-11-26 - <artifact>, <detail>)` to all 10 goal lines.

**Result**: `goal_ledger.py --status mechanic` → 10/10 reached [OK]. Fleet total went 73→83 (75%).
