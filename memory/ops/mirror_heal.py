#!/usr/bin/env python3
"""mirror_heal.py - detect missed mirror syncs and auto-repair.

Runs every 15 min via schtask 'MirrorHeal'. Checks memory_mirror.log for the
last successful run; if older than MAX_AGE_S, re-triggers memory_mirror.py.
Logs all actions to memory/mechanic/mirror-repairs.jsonl.
Alerts only on repeated failures (>3 in one hour).

Recreated 2026-11-17 after mirror revert (4th occurrence of this pattern).
Spec: memory/mechanic/goal2_mirror_heal_productionized-2026-11-17.md
"""
import json, os, subprocess, sys, datetime, time

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (script is at memory/ops/)
MIRROR_LOG = os.path.join(HERE, "memory_mirror.log")
REPAIR_LOG = os.path.join(HERE, "memory", "mechanic", "mirror-repairs.jsonl")
MIRROR_SCRIPT = os.path.join(HERE, "memory_mirror.py")
MAX_AGE_S = 900        # 15 minutes
ALERT_THRESHOLD = 3    # alert after >3 failures in one hour
DRY_RUN = "--dry-run" in sys.argv


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _log(entry):
    entry["ts"] = _now().isoformat()
    os.makedirs(os.path.dirname(REPAIR_LOG), exist_ok=True)
    with open(REPAIR_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _last_sync_time():
    """Parse memory_mirror.log and return the timestamp of the last run."""
    if not os.path.exists(MIRROR_LOG):
        return None
    last_ts = None
    with open(MIRROR_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                t_str = obj.get("t", "")
                # format: "2026-11-17 20:27:20"
                dt = datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=datetime.timezone.utc
                )
                last_ts = dt
            except (json.JSONDecodeError, ValueError):
                continue
    return last_ts


def _recent_failures():
    """Count repair failures in the last hour from REPAIR_LOG."""
    if not os.path.exists(REPAIR_LOG):
        return 0
    cutoff = (_now() - datetime.timedelta(hours=1)).isoformat()
    count = 0
    with open(REPAIR_LOG) as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                if obj.get("ts", "") >= cutoff and obj.get("type") == "repair_failed":
                    count += 1
            except json.JSONDecodeError:
                continue
    return count


def main():
    last = _last_sync_time()
    now = _now()

    if last is None:
        detail = "no mirror log found - cannot determine staleness"
        if not DRY_RUN:
            _log({"type": "repair_failed", "detail": detail})
        else:
            print(f"DRY-RUN: {detail}")
        return

    age_s = (now - last).total_seconds()
    stale = age_s > MAX_AGE_S

    if not stale:
        if DRY_RUN:
            print(f"DRY-RUN: mirror fresh ({age_s:.0f}s < {MAX_AGE_S}s) - no action")
        return

    # Stale detected
    if DRY_RUN:
        print(f"DRY-RUN: STALE detected ({age_s:.0f}s > {MAX_AGE_S}s), would re-run mirror")
        _log({"type": "dry_run", "detail": f"stale detection fired, no action taken",
              "age_s": round(age_s)})
        return

    # Attempt repair: re-run memory_mirror.py
    try:
        r = subprocess.run(
            [sys.executable, MIRROR_SCRIPT],
            capture_output=True, text=True, timeout=120,
            cwd=HERE,
        )
        if r.returncode == 0:
            _log({"type": "repair_ok", "detail": f"mirror re-run succeeded after {age_s:.0f}s stale",
                  "age_s": round(age_s)})
        else:
            err = (r.stderr or r.stdout or "")[:200]
            failures = _recent_failures() + 1
            entry = {"type": "repair_failed", "detail": f"mirror re-run rc={r.returncode}: {err}",
                     "age_s": round(age_s), "failures_last_hour": failures}
            if failures > ALERT_THRESHOLD:
                entry["ALERT"] = True
                entry["alert_msg"] = (f"MirrorHeal: {failures} failures in last hour - "
                                       f"check SMB creds / host availability")
            _log(entry)
    except subprocess.TimeoutExpired:
        _log({"type": "repair_failed", "detail": "mirror re-run timed out (120s)",
              "age_s": round(age_s)})
    except Exception as e:
        _log({"type": "repair_failed", "detail": f"exception: {e}", "age_s": round(age_s)})


if __name__ == "__main__":
    main()
