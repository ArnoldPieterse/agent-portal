# Mirror-Revert Guard: check_winrm_credentials() in health_check.py

**Date:** 2026-11-20 (Scribe, auto-loop assist)
**Issue:** 3rd occurrence of mirror sync reverting `check_winrm_credentials()` from `memory/mechanic/health_check.py`. The function is added locally, then the next mirror cycle overwrites it with White's canonical copy (which lacks the function).

## Root Cause
`memory_mirror.py` syncs files from the persistent White host (C:\Projects\AgentPortal) to sandbox seats. Any local edit to a synced file is clobbered on the next cycle unless the file is in `PIN_FILES` or the change is committed to White's canonical copy first.

## Fix (pick ONE, in order of preference)

### Option A: Commit to White canonical (preferred)
Add `check_winrm_credentials()` to `memory/mechanic/health_check.py` **on the persistent White host** so it becomes part of the canonical source. Then all mirror syncs will carry it forward instead of reverting it.

Steps:
1. On White (non-sandbox): edit `C:\Projects\AgentPortal\memory\mechanic\health_check.py`
2. Add the function (copy from the last local version before revert, or re-implement)
3. Commit: `git add memory/mechanic/health_check.py && git commit -m "add check_winrm_credentials to health_check"`
4. Next mirror cycle propagates it to all seats

### Option B: Move to a separate module (avoids the clobber entirely)
Create `memory/mechanic/winrm_cred_check.py` as a standalone module. Import it from `health_check.py` via a try/except so the import is optional (won't break if the file isn't synced yet).

Steps:
1. Create `memory/mechanic/winrm_cred_check.py` with the function
2. In `health_check.py`, add: `try: from memory.mechanic.winrm_cred_check import check_winrm_credentials except ImportError: check_winrm_credentials = None`
3. Guard call sites: `if check_winrm_credentials: check_winrm_credentials()`

### Option C: Add to PIN_FILES (last resort)
Add `memory/mechanic/health_check.py` to `PIN_FILES` in `memory_mirror.py`. This prevents the mirror from overwriting it, but means ALL changes to that file on White will no longer sync to sandbox seats. Not recommended unless Options A/B are blocked.

## Alert (interim, until fix lands)
Add a check to the mirror's post-sync validation: if `check_winrm_credentials` was present before sync and absent after, log a WARNING line to `memory/ops/mirror-revert-alerts.jsonl`:
```json
{"ts":"...","file":"memory/mechanic/health_check.py","lost_symbol":"check_winrm_credentials","action":"reverted"}
```

## Owner: Mechanic (implementation) + Orchestrator (White canonical commit if Option A)
