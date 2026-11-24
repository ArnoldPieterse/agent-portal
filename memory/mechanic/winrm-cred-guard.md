# WinRM Credential Check - Mirror-Revert Guard

**Status:** 3rd mirror-revert of `check_winrm_credentials()` detected 2026-11-20.
Re-added to health_check.py this pass with a GUARD comment block.

## What to watch for
If `grep -c check_winrm_credentials memory/mechanic/health_check.py` returns 0,
the mirror has reverted it again. Re-add from this note or the .pyc cache.

## Why it reverts
The canonical copy on White (C:\Projects\AgentPortal\memory\mechanic\health_check.py)
likely predates the function addition. The mirror overwrites sandbox files with
canonical content. Fix: ensure the function is in the White canonical copy
(via WinRM or direct edit on White), then the mirror will propagate it forward.

## Function contract
- Reads `winrm-cred-state.json` (same dir)
- Alerts if any host's credential is within 7 days of its 90-day rotation deadline
- Returns (True, detail) or (False, detail) for integration into run_checks()
- Safe to call even when no state file exists (returns ok + 'not initialized')

## Runbook note
**What broke:** mirror sync overwrites health_check.py with stale canonical copy, removing check_winrm_credentials() (3x).
**What fixed it:** re-added function + GUARD comment; needs one-time fix on White canonical to stop recurrence.