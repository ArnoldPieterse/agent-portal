#!/usr/bin/env python3
"""gap_alarm.py (2026-11-23, White ops): fleet-silence alarm.

Runs every 5 min via schtask PortalGapAlarm (same pattern as MirrorSync).
If the repo HEAD has not changed for > GAP_MIN minutes while a goal cycle is
open and incomplete, write memory/ops/gap_alarm.json (flag) + append to
memory/ops/gap-alarm.log. Fresh commit -> flag cleared.

This surfaces portal/fleet stalls within ~65 min instead of silently
consuming them (cycle-8 sat 35h un-leveled before anyone noticed).
"""
import json, os, subprocess, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_MIN = 60
FLAG = os.path.join(HERE, "memory", "ops", "gap_alarm.json")
LOG = os.path.join(HERE, "memory", "ops", "gap-alarm.log")
GIT = os.path.join(HERE, "mingit", "cmd", "git.exe")


def head_age_s():
    try:
        r = subprocess.run([GIT, "log", "-1", "--pretty=format:%ct"], cwd=HERE,
                           capture_output=True, timeout=30)
        return time.time() - int(r.stdout.decode().strip())
    except Exception:
        return None


def goals_open():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8099/api/goals", timeout=10) as r:
            d = json.load(r)
        items = d.get("goals") or d.get("items") or []
        if not items:
            return False, 0
        reached = sum(1 for g in items if (g.get("reached") is True or str(g.get("reached", "")).lower() == "true"))
        return reached < len(items), round(100.0 * reached / len(items))
    except Exception:
        return None, 0   # portal unreachable -> watchdog's job, not this alarm's


def main():
    age = head_age_s()
    if age is None:
        return
    open_cycle, pct = goals_open()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if age > GAP_MIN * 60 and open_cycle is True:
        flag = {"active": True, "since_min": int(age // 60), "pct": pct, "ts": now}
        try:
            os.makedirs(os.path.dirname(FLAG), exist_ok=True)
            with open(FLAG, "w") as f:
                json.dump(flag, f)
            with open(LOG, "a") as f:
                f.write("%s GAP: no commit for %d min, cycle open at %d%%\n" % (now, flag["since_min"], pct))
        except Exception:
            pass
    elif age <= GAP_MIN * 60 and os.path.exists(FLAG):
        try:
            with open(LOG, "a") as f:
                f.write("%s clear: commit activity resumed\n" % now)
            os.remove(FLAG)
        except Exception:
            pass


if __name__ == "__main__":
    main()
