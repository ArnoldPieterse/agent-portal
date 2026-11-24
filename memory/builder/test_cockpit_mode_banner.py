"""Cockpit Mode Banner - Builder goal #2 selftest.
Verifies: (a) fleet-mode.json is valid, (b) _cockpit_snapshot code produces
fleet_mode key with correct shape, (c) cockpit.js renders from that shape."""
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent.parent
FLEET_MODE_FILE = HERE / "fleet-mode.json"
PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print("  [PASS] " + name)
    else: FAIL += 1; print("  [FAIL] " + name)
print("Cockpit Mode Banner selftest (Builder goal #2)")
# 1. fleet-mode.json exists and is valid
fm_data = None
if FLEET_MODE_FILE.exists():
    fm_data = json.loads(FLEET_MODE_FILE.read_text(encoding="utf-8"))
check("fleet-mode.json exists", fm_data is not None)
if fm_data:
    check("mode is valid enum", fm_data.get("mode") in ("WORK","MAINTENANCE","IDLE"))
    check("timestamp is ISO-8601", bool(fm_data.get("timestamp")))
    check("goal_pct is numeric 0-100", isinstance(fm_data.get("goal_pct"),(int,float)) and 0 <= fm_data["goal_pct"] <= 100)
# 2. Simulate _cockpit_snapshot fleet_mode extraction (same logic as agent_portal.py L1675-1693)
def simulate_cockpit_fleet_mode():
    try:
        with open(FLEET_MODE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        ts_str = raw.get("timestamp", "")
        elapsed_h = None
        if ts_str:
            try:
                parsed = datetime.fromisoformat(ts_str.replace("Z","+00:00"))
                elapsed_h = round((time.time() - parsed.timestamp()) / 3600, 2)
            except (ValueError, OSError):
                pass
        return {"mode": raw.get("mode","WORK"), "goal_pct": raw.get("goal_pct"),
                "elapsed_since_activity_h": elapsed_h, "timestamp": ts_str}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
fm_out = simulate_cockpit_fleet_mode()
check("fleet_mode key is produced", fm_out is not None)
if fm_out:
    check("has mode field", "mode" in fm_out)
    check("has elapsed_since_activity_h field", "elapsed_since_activity_h" in fm_out)
    check("has goal_pct field", "goal_pct" in fm_out)
    check("elapsed is numeric or None", fm_out["elapsed_since_activity_h"] is None or isinstance(fm_out["elapsed_since_activity_h"], (int,float)))
# 3. Verify agent_portal.py contains the code
ap = HERE / "agent_portal.py"
ap_text = ap.read_text(encoding="utf-8")
check("agent_portal.py has fleet_mode in cockpit data dict", '"fleet_mode": fm_out' in ap_text)
check("agent_portal.py reads _FLEET_MODE_PATH in snapshot", '_fm_raw = json.load(_f)' in ap_text)
# 4. Verify cockpit.js renders from d.fleet_mode
ckp_js = HERE / "ui" / "cockpit.js"
js_text = ckp_js.read_text(encoding="utf-8")
check("cockpit.js reads d.fleet_mode", "d.fleet_mode" in js_text)
check("cockpit.js has mode colors", 'modeColors' in js_text)
check("cockpit.js has elapsed display", 'elapsed_since_activity_h' in js_text)
print(f"\nResult: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)