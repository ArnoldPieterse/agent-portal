#!/usr/bin/env python3
"""mode_transition_test.py - Verifier G1 (cycle-15): 99% -> 100% integration test.

In an isolated sandbox root:
  a. fleet-mode.json updates within ONE pass cycle (one fleet_mode.main() call):
     99% open goal -> mode WORK; flip the last goal to reached -> pct 100, mode MAINTENANCE
  b. dispatch text switches from the open-goal list to the role maintenance task
     (canonical dispatch_filter, same rules as the portal autoloop)
  c. cockpit banner contract: live /api/fleet/mode returns {mode, goal_pct} and the
     UI maps MAINTENANCE -> amber 'mode-maintenance' class (checked in ui/cockpit.js)

Usage:
  python mode_transition_test.py
"""
import importlib.util, json, shutil, sys, tempfile, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    fm = load("fleet_mode", HERE / "memory" / "orchestrator" / "fleet_mode.py")
    df = load("dispatch_filter", HERE / "memory" / "orchestrator" / "dispatch_filter.py")

    tmp = Path(tempfile.mkdtemp(prefix="mtr_"))
    try:
        goals = tmp / "memory" / "goals"
        ops = tmp / "memory" / "ops"
        goals.mkdir(parents=True); ops.mkdir()
        # 100-goal set: 99 reached + 1 open (99%)
        lines = [f"{i}. **Goal {i}** - task (verified: 2026-11-24 - done)" for i in range(1, 100)]
        lines.append("100. **Final goal** - the last one")
        (goals / "orchestrator.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        # recent activity signal -> MAINTENANCE (not IDLE) once at 100%
        (ops / "fleet-snapshots.jsonl").write_text(json.dumps({"ts": datetime.now(timezone.utc).isoformat()}) + "\n", encoding="utf-8")

        fm.BASE = tmp; fm.GOALS_DIR = goals; fm.OPS_DIR = ops; fm.OUTPUT_FILE = ops / "fleet-mode.json"

        # --- state A: 99% -> WORK, dispatch = goal list ---
        fm.main()
        a = json.loads(fm.OUTPUT_FILE.read_text(encoding="utf-8"))
        assert a["goal_pct"] == 99.0 and a["mode"] == "WORK", a
        da = df.dispatch("orchestrator", open_goals=["Final goal"], reached_goals=[f"Goal {i}" for i in range(1, 100)],
                         mode=a["mode"])
        assert da["kind"] == "goal" and "Final goal" in da["text"], da
        assert "Goal 50" not in da["text"], "reached goals must not appear in dispatch text"

        # --- flip last goal to reached; ONE pass cycle ---
        (goals / "orchestrator.md").write_text(
            ("\n".join(lines) + "\n").replace("100. **Final goal** - the last one",
                                               "100. **Final goal** - the last one (verified: 2026-11-24 - done)"),
            encoding="utf-8")
        t_before = time.time()
        fm.main()   # exactly one pass cycle
        b = json.loads(fm.OUTPUT_FILE.read_text(encoding="utf-8"))
        assert b["goal_pct"] == 100.0 and b["goals_open"] == 0, b
        assert b["mode"] == "MAINTENANCE", f"expected MAINTENANCE at 100% with fresh activity, got {b['mode']}"
        assert time.time() - t_before < 5, "one pass cycle must be fast (no blocking)"

        # --- dispatch switches to the role maintenance task ---
        db = df.dispatch("orchestrator", open_goals=[], reached_goals=[f"Goal {i}" for i in range(1, 101)],
                         mode=b["mode"])
        assert db["kind"] == "maintenance", db
        rot = df.rotation_task("orchestrator")
        assert rot and rot.split(" (")[0] in db["text"], (db, rot)
        assert db["text"] != da["text"] and "Final goal" not in db["text"]

        # --- cockpit banner contract: live API + UI class mapping ---
        with urllib.request.urlopen("http://127.0.0.1:8099/api/fleet/mode", timeout=5) as r:
            live = json.loads(r.read().decode())
        assert "mode" in live and "goal_pct" in live, live
        ui = (HERE / "ui" / "cockpit.js").read_text(encoding="utf-8")
        assert "mode-maintenance" in ui and "mode-work" in ui, "UI must map modes to banner classes"

        print(f"SELFTEST OK (99% WORK -> 100% MAINTENANCE in one pass cycle; dispatch goal-list -> maintenance task '{rot}'; live /api/fleet/mode {live.get('mode')} {live.get('goal_pct')}%; UI maps mode->banner class)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())