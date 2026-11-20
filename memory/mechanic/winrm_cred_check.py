"""
winrm_cred_check.py - Standalone WinRM credential rotation check.
Extracted from health_check.py to survive mirror-revert (3rd occurrence 2026-11-20).
Safe to import standalone; no dependency on health_check internals.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

WINRM_CRED_STATE = Path(__file__).parent / "winrm-cred-state.json"
WINRM_ROTATION_DAYS = 90
WINRM_ALERT_WINDOW_DAYS = 7  # alert if within 7 days of expiry


def check_winrm_credentials():
    """Check WinRM credential rotation state. Alerts if any credential is within
    WINRM_ALERT_WINDOW_DAYS of its 90-day rotation deadline.
    Returns (ok, detail). If no state file exists, returns ok with 'no state' note."""
    if not WINRM_CRED_STATE.exists():
        return True, "no cred-state file (rotation not yet initialized)"
    try:
        with open(WINRM_CRED_STATE, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"cred-state unreadable: {e}"

    now = datetime.now(timezone.utc)
    expiring = []
    for host, info in state.get("hosts", {}).items():
        last_rotated = info.get("last_rotated")
        if not last_rotated:
            continue
        try:
            rot_dt = datetime.fromisoformat(last_rotated)
        except ValueError:
            continue
        days_since = (now - rot_dt).days
        days_until_expiry = WINRM_ROTATION_DAYS - days_since
        if days_until_expiry <= WINRM_ALERT_WINDOW_DAYS:
            expiring.append(f"{host} ({days_until_expiry}d left)")

    if expiring:
        return False, f"credentials expiring soon: {expiring}"
    host_count = len(state.get("hosts", {}))
    return True, f"all {host_count} hosts within rotation window"
