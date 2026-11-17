#!/usr/bin/env python3
"""
schtasks_dep_capture.py (2026-11-18, Mechanic goal #6)
One-shot: capture live schtasks CSV + generate dependency graph baseline.
Run from a non-sandbox seat (White ops terminal / RDP) where COM is available.

Usage:
  python memory/ops/schtasks_dep_capture.py [--week N]

Output:
  memory/mechanic/dep-snapshots/week-N.csv       (raw schtasks CSV)
  memory/mechanic/dep-snapshots/week-N-graph.json (parsed graph + edges)
  If week-(N-1) exists, includes diff in the graph JSON.
"""
import subprocess, sys, os, datetime, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # project root
SNAP_DIR = os.path.join(ROOT, "memory", "mechanic", "dep-snapshots")
GEN_SCRIPT = os.path.join(HERE, "schtask_dep_gen.py")

def main():
    week = 1
    if "--week" in sys.argv:
        idx = sys.argv.index("--week")
        week = int(sys.argv[idx + 1])

    os.makedirs(SNAP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_path = os.path.join(SNAP_DIR, f"week-{week}.csv")
    json_path = os.path.join(SNAP_DIR, f"week-{week}-graph.json")

    # Step 1: capture schtasks CSV
    print(f"[1/3] Capturing schtasks /query /fo CSV /v ...")
    r = subprocess.run(
        ["schtasks", "/query", "/fo", "CSV", "/v"],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        print(f"FATAL: schtasks failed rc={r.returncode}: {r.stderr.strip()[:200]}", file=sys.stderr)
        sys.exit(1)

    with open(csv_path, "w", encoding="utf-8-sig") as f:
        f.write(r.stdout)
    line_count = r.stdout.count("\n")
    print(f"      -> {csv_path} ({line_count} lines)")

    # Step 2: generate graph (with prev-week diff if available)
    print(f"[2/3] Generating dependency graph ...")
    cmd = [sys.executable, GEN_SCRIPT, "--input", csv_path, "--output", json_path]
    prev_json = os.path.join(SNAP_DIR, f"week-{week-1}-graph.json")
    prev_csv = os.path.join(SNAP_DIR, f"week-{week-1}.csv")
    if os.path.exists(prev_csv):
        cmd.extend(["--prev", prev_csv])
        print(f"      (diffing against week-{week-1})")

    r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r2.returncode != 0:
        print(f"FATAL: dep_gen failed: {r2.stderr.strip()[:200]}", file=sys.stderr)
        sys.exit(1)
    print(r2.stdout.strip())
    if r2.stderr.strip():
        print(r2.stderr.strip(), file=sys.stderr)

    # Step 3: summary
    print(f"[3/3] Baseline captured.")
    with open(json_path) as f:
        g = json.load(f)
    print(f"      Host: {g['host']}, Tasks: {g['task_count']}, Edges: {len(g['edges'])}")
    if "diff" in g:
        d = g["diff"]
        print(f"      Diff vs week-{week-1}: +{len(d['added'])} added, -{len(d['removed'])} removed")
        if d["added"]:
            print(f"      ADDED: {d['added']}")
        if d["removed"]:
            print(f"      REMOVED: {d['removed']}")
    else:
        print(f"      (first snapshot - no diff)")
    print(f"\nDone. Next week: python memory/ops/schtasks_dep_capture.py --week {week+1}")

if __name__ == "__main__":
    main()
