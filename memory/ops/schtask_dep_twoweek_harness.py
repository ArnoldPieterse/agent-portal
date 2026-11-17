#!/usr/bin/env python3
"""
schtask_dep_twoweek_harness.py (2026-11-18, Mechanic goal #6 cycle-3)

Exercises the FULL weekly-generation + diff pipeline of schtask_dep_gen.py
end-to-end on a deterministic fixture, producing dated baseline artifacts:
  dep-snapshots/week-1.csv  -> week-1-graph.json
  dep-snapshots/week-2.csv  -> week-2-graph.json   (diff vs week-1)

This proves goal #6 closure criterion "two weekly generations with correct
diff; one test task addition correctly flagged" WITHOUT needing a live
schtasks COM session: the fixture stands in for the real snapshot. When White
captures the first real CSV, the identical two-week flow runs on real data.

Usage:
  python memory/ops/schtask_dep_twoweek_harness.py
Exit 0 = PASS (all assertions hold), 1 = FAIL.
"""
import csv, json, os, sys, subprocess, io, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "schtask_dep_gen.py")
SNAPDIR = os.path.normpath(os.path.join(HERE, "..", "mechanic", "dep-snapshots"))

# Deterministic fixture: the fleet's real scheduled-task set (week 1).
WEEK1_TASKS = [
    "\\PortalRun",
    "\\PortalDailyGitCommit",
    "\\FleetProbe",
    "\\AgentGroupChat",
    "\\MemoryMirrorRun",
    "\\RemoteMemoryFreshness",
]
# Week 2 = week 1 + one deliberately-added test task (the thing to be flagged).
TEST_TASK_ADDED = "\\TestTaskAddition"
WEEK2_TASKS = WEEK1_TASKS + [TEST_TASK_ADDED]

CSV_HEADER = "Task Name,Schedule Type,Status,Next Run Time\n"

def write_fixture(path, tasks):
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(CSV_HEADER)
        for t in tasks:
            f.write(f'"{t}",Daily,Ready,01/01/2026 03:00:00\n')

def run_gen(input_csv, prev_csv=None, output_json=None):
    cmd = [sys.executable, GEN, "--input", input_csv]
    if prev_csv:
        cmd += ["--prev", prev_csv]
    if output_json:
        cmd += ["--output", output_json]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p

def main():
    os.makedirs(SNAPDIR, exist_ok=True)
    w1 = os.path.join(SNAPDIR, "week-1.csv")
    w2 = os.path.join(SNAPDIR, "week-2.csv")
    g1 = os.path.join(SNAPDIR, "week-1-graph.json")
    g2 = os.path.join(SNAPDIR, "week-2-graph.json")

    write_fixture(w1, WEEK1_TASKS)
    write_fixture(w2, WEEK2_TASKS)

    # Generation 1: baseline (no prev).
    p1 = run_gen(w1, None, g1)
    if p1.returncode != 0:
        print("FAIL week-1 gen:\n" + p1.stderr); return 1

    # Generation 2: diff vs week-1. Capture the ALERT for the added task.
    p2 = run_gen(w2, w1, g2)
    if p2.returncode != 0:
        print("FAIL week-2 gen:\n" + p2.stderr); return 1

    # Load both graphs and assert correctness.
    jg1 = json.load(open(g1))
    jg2 = json.load(open(g2))

    checks = []
    def ck(name, cond):
        checks.append((name, bool(cond)))

    ck("week-1 task_count == 6", jg1["task_count"] == 6)
    ck("week-2 task_count == 7", jg2["task_count"] == 7)
    ck("week-1 has edges (inferred)", len(jg1["edges"]) >= 4)

    d = jg2.get("diff", {})
    added = [t for t in d.get("added", [])]
    removed = [t for t in d.get("removed", [])]
    ck("exactly one task ADDED (the test task)",
       len(added) == 1 and TEST_TASK_ADDED in added)
    ck("nothing REMOVED week1->week2", len(removed) == 0)
    ck("ALERT NEW emitted to stderr for added task",
       "ALERT NEW" in p2.stderr and TEST_TASK_ADDED in p2.stderr)

    ok = all(c for _, c in checks)
    stamp = datetime.datetime.now().isoformat()
    report = {
        "generated": stamp,
        "harness": "schtask_dep_twoweek_harness.py",
        "mode": "deterministic-fixture (stand-in for real schtasks snapshot)",
        "artifacts": {"week-1.csv": w1, "week-2.csv": w2,
                     "week-1-graph.json": g1, "week-2-graph.json": g2},
        "diff_added": added, "diff_removed": removed,
        "checks": {n: c for n, c in checks},
        "verdict": "PASS" if ok else "FAIL",
    }
    rep = os.path.join(SNAPDIR, "twoweek-diff-report.json")
    json.dump(report, open(rep, "w"), indent=2)

    # Append evidence line.
    ev = os.path.normpath(os.path.join(HERE, "..", "mechanic",
                                        "goal6-dep-gen-twoweek-evidence.jsonl"))
    with open(ev, "a") as f:
        f.write(json.dumps(report) + "\n")

    for n, c in checks:
        print(("PASS " if c else "FAIL ") + n)
    print("VERDICT: " + ("PASS" if ok else "FAIL"))
    print("report ->", rep.replace(os.sep, "/"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())