#!/usr/bin/env python3
"""heartbeat_pass_hook.py - Auto-refresh fleet heartbeat on pass start (idempotent).

Eliminates the recurring 2x/day manual remediation cycle by checking staleness
and refreshing automatically when an agent pass begins.

Usage:
    python memory/ops/heartbeat_pass_hook.py [--force]

Behaviour:
    - If fleet-heartbeat.json is <30min old: no-op (exit 0)
    - If stale or missing: runs seat_probe.py --force + fleet_heartbeat.py generate
    - Logs action to memory/ops/heartbeat-pass-hook.jsonl
    - Exit 0 = fresh or refreshed; exit 1 = refresh failed

Aligned with round topic: Fleet Autonomy Convergence (removes manual touch point).
"""
import json, sys, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(".")
HEARTBEAT = BASE / "memory" / "ops" / "fleet-heartbeat.json"
LOG = BASE / "memory" / "ops" / "heartbeat-pass-hook.jsonl"
STALE_THRESHOLD_S = 1800  # 30 minutes

def log_event(action, detail=""):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail,
        "agent": "mechanic"
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def check_age():
    """Return age in seconds of heartbeat file, or None if missing."""
    if not HEARTBEAT.exists():
        return None
    try:
        data = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(data["ts"])
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age
    except Exception:
        return None

def refresh():
    """Run seat_probe + heartbeat generate. Return (success, detail)."""
    try:
        r1 = subprocess.run(
            [sys.executable, str(BASE / "memory" / "mechanic" / "seat_probe.py"), "--force"],
            capture_output=True, text=True, timeout=30
        )
        r2 = subprocess.run(
            [sys.executable, str(BASE / "memory" / "mechanic" / "fleet_heartbeat.py"), "generate"],
            capture_output=True, text=True, timeout=15
        )
        if r2.returncode == 0:
            return True, f"probe_rc={r1.returncode} gen_rc=0"
        else:
            return False, f"probe_rc={r1.returncode} gen_rc={r2.returncode} stderr={r2.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)

def main():
    force = "--force" in sys.argv
    
    age = check_age()
    
    if not force and age is not None and age < STALE_THRESHOLD_S:
        log_event("skip", f"fresh (age={age:.0f}s)")
        print(f"OK: heartbeat fresh ({age:.0f}s old), no action needed")
        return 0
    
    reason = "forced" if force else (f"stale (age={age:.0f}s)" if age is not None else "missing")
    t0 = time.time()
    ok, detail = refresh()
    elapsed = time.time() - t0
    
    action = "refreshed" if ok else "refresh_failed"
    log_event(action, f"{reason} in {elapsed:.1f}s: {detail}")
    
    if ok:
        print(f"OK: heartbeat refreshed ({reason}, {elapsed:.1f}s)")
        return 0
    else:
        print(f"FAIL: refresh failed ({reason}): {detail}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
