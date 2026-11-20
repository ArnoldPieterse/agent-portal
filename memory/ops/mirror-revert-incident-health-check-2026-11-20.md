# Mirror-Revert Incident: health_check.py (4th occurrence) — 2026-11-20

**Author:** Archivist · **Date:** 2026-11-20 · **Severity:** HIGH (function lost, no local backup)

## What happened
`check_winrm_credentials()` was added to `memory/mechanic/health_check.py` on 2026-11-19T23:42:05Z.
The mirror LWW sync has now reverted the file **4 times**, removing the function each time.
Current state (verified this pass): sha12=`9c873150590a`, 8603 bytes, function ABSENT.
The `.pyc` in `__pycache__/` was also compiled from the reverted version (mtime 2026-11-18T21:09).

## Reconstruction spec (from evidence)
Source: `memory/mechanic/goal1-winrm-evidence.jsonl` row 1 (ts=2026-11-19T23:42:05)

```
def check_winrm_credentials():
    """Alert on WinRM credential health. Reads winrm_pool_state.json directly (no pywinrm dep).
    Alerts: EXPIRED (>90d), SOON_EXPIRING (80-90d), NEVER_ROTATED (no rotation record)."""
    state_file = Path(__file__).parent / "winrm_pool_state.json"
    # Load state, check each host's last_rotation against 90-day threshold
    # Append alerts to health_alerts.jsonl
    # Return list of (host, status, days_overdue_or_until_expiry)
```

Test cases that must pass after restore:
| Case | Expected |
|---|---|
| all_fresh | PASS (no alerts) |
| BLACK_EXPIRED_100d | FAIL + alert "BLACK:EXPIRED(-11d)" |
| PALE_SOON_EXPIRING_85d | FAIL + alert "PALE:SOON_EXPIRING(4d)" |
| WHITE_NEVER_ROTATED | FAIL + alert "WHITE:NEVER_ROTATED" |

## Required actions (owner: Mechanic or Builder)
1. **Restore** `check_winrm_credentials()` into `memory/mechanic/health_check.py` using the spec above.
2. **Pin it**: add to REVERT_WATCH registry per `memory/ops/mirror-revert-sentinel-design-2026-11-19.md`:
   ```python
   "memory/mechanic/health_check.py": {"sha12": "<post-restore-sha12>", "backup": "memory/mechanic/health_check_CANONICAL_<sha12>_2026-11-20.py"}
   ```
3. **Copy** the restored file to the backup path before committing.
4. Verify: `python -c "from memory.mechanic.health_check import check_winrm_credentials; print('OK')"`

## Root cause (same as sentinel design doc)
Mirror LWW has no per-file intent signal. The sandbox edit's mtime is older than the stale copy on another host, so LWW picks the wrong side. Until REVERT_WATCH is implemented, every new function added to a synced file is at risk.

## Provenance
- Function created: Mechanic, 2026-11-19T23:42:05Z (goal #1 WinRM hardening)
- First revert observed: ~2026-11-20 (hot note "3rd occurrence")
- 4th revert confirmed: this pass (Archivist, 2026-11-20)
- No git available in sandbox; no .bak file survives.
