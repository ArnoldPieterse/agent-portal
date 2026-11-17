#!/usr/bin/env python3
"""
schtask_dep_gen.py (2026-11-17, Mechanic goal #6 cycle-3)
Auto-generate scheduled-task dependency graph from schtasks /query CSV output.

Usage:
  python memory/ops/schtask_dep_gen.py --input snapshot.csv [--prev prev_snapshot.csv]
"""
import csv, json, sys, os, argparse, datetime, io

KNOWN_DEPS = {
    "PortalRun": ["PortalDailyGitCommit", "FleetProbe", "AgentGroupChat"],
    "MemoryMirrorRun": ["RemoteMemoryFreshness"],
    "PortalDailyGitCommit": [],
    "PortalFleetProbe": [],
    "RecoverAll": [],
}

def parse_schtasks_csv(text):
    tasks = []
    text = text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        name = (row.get("Task Name") or row.get("TaskName") or "").strip()
        if not name or name in ("Task Name", "TaskName"):
            continue
        tasks.append({
            "name": name,
            "status": (row.get("Status") or "").strip(),
            "schedule_type": (row.get("Schedule Type") or row.get("ScheduleType") or "").strip(),
            "next_run": (row.get("Next Run Time") or row.get("NextRunTime") or "").strip()
        })
    return tasks

def _clean_task_name(raw):
    BS = chr(92)
    parts = raw.replace("/", BS).split(BS)
    return parts[-1] if parts else raw

def infer_edges(tasks):
    edges = []
    for t in tasks:
        clean = _clean_task_name(t["name"]).lower()
        for known, deps in KNOWN_DEPS.items():
            if known.lower() in clean:
                for dep in deps:
                    edges.append({"from": t["name"], "to": dep, "type": "known"})
    return edges

def diff_tasks(prev_tasks, curr_tasks):
    prev_names = {t["name"] for t in prev_tasks}
    curr_names = {t["name"] for t in curr_tasks}
    return {"added": sorted(curr_names - prev_names), "removed": sorted(prev_names - curr_names)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--prev")
    ap.add_argument("--output")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8-sig") as f:
        tasks = parse_schtasks_csv(f.read())

    result = {
        "generated": datetime.datetime.now().isoformat(),
        "host": os.environ.get("COMPUTERNAME", "unknown"),
        "task_count": len(tasks),
        "tasks": tasks,
        "edges": infer_edges(tasks),
    }

    if args.prev and os.path.exists(args.prev):
        with open(args.prev, encoding="utf-8-sig") as f:
            prev_tasks = parse_schtasks_csv(f.read())
        result["diff"] = diff_tasks(prev_tasks, tasks)
        d = result["diff"]
        if d["added"]:
            print("ALERT NEW: " + ", ".join(d["added"]), file=sys.stderr)
        if d["removed"]:
            print("ALERT REMOVED: " + ", ".join(d["removed"]), file=sys.stderr)

    out = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Wrote {args.output} ({len(tasks)} tasks, {len(result[chr(101)+chr(100)+chr(103)+chr(101)+chr(115)])} edges)")
    else:
        print(out)

if __name__ == "__main__":
    main()
