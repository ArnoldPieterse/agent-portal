#!/usr/bin/env python3
"""Autonomy Stall Detector (Verifier goal #3).

Flags any agent whose lane shows ZERO file changes across N consecutive
auto-loop passes. Pure filesystem-state diagnostic: no network, no COM,
no browser - runs clean in a sandbox seat.

A "pass" is one recorded snapshot of each lane's newest tracked-file mtime.
An agent is STALLED when its newest mtime does not advance across the last
`threshold` snapshots (default 3).

Usage:
  python stall_detector.py --scan [--root DIR] [--state FILE]
      record one pass snapshot of live lanes under memory/
  python stall_detector.py --check [--state FILE] [--threshold N]
      report agents stalled across the last N recorded passes
  python stall_detector.py --selftest
      end-to-end proof on a temp tree (simulated lanes + passes)
"""
import argparse, json, os, sys, time, tempfile, pathlib

LANES = ["orchestrator", "researcher", "verifier", "scribe",
         "designer", "builder", "archivist", "mechanic"]
TRACK_EXT = (".md", ".py", ".json", ".jsonl")
DEFAULT_STATE = str(pathlib.Path(__file__).with_name("stall_state.jsonl"))


def lane_newest_mtime(lane_dir):
    """Newest mtime among tracked files in a lane dir (recursive), or None."""
    newest = None
    for dp, _dn, fn in os.walk(str(lane_dir)):
        for name in fn:
            if name.endswith(TRACK_EXT):
                try:
                    mt = os.path.getmtime(os.path.join(dp, name))
                except OSError:
                    continue
                if newest is None or mt > newest:
                    newest = mt
    return newest


def scan_lanes(root, lanes=None):
    """Map lane -> newest mtime for every known lane under root."""
    out = {}
    for lane in (lanes or LANES):
        d = os.path.join(str(root), lane)
        if os.path.isdir(d):
            out[lane] = lane_newest_mtime(d)
    return out


def record_pass(state_path, lanes_state, pass_id=None):
    rec = {"ts": time.time(), "pass_id": pass_id or int(time.time()),
           "lanes": lanes_state}
    with open(state_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def load_passes(state_path):
    if not os.path.exists(state_path):
        return []
    rows = []
    with open(state_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def detect_stalls(state_path, threshold=3):
    """Return {agent: {stalled, unchanged_passes, evidence}} for agents whose
    newest mtime did not advance across the last `threshold` passes."""
    passes = load_passes(state_path)
    result = {}
    if len(passes) < threshold:
        return result  # not enough history yet
    recent = passes[-threshold:]
    agents = set()
    for p in recent:
        agents |= set(p.get("lanes", {}))
    for agent in sorted(agents):
        mts = [p["lanes"].get(agent) for p in recent]
        if None in mts:
            continue  # lane absent in some pass -> not a stall, skip
        distinct = len(set(mts))
        stalled = distinct == 1  # identical newest-mtime across all `threshold`
        result[agent] = {
            "stalled": stalled,
            "unchanged_passes": threshold if stalled else None,
            "newest_mtime": mts[-1],
            "evidence": [round(m, 3) for m in mts],
        }
    return result


def _selftest():
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok = ok and cond

    tmp = tempfile.mkdtemp(prefix="stall_")
    root = os.path.join(tmp, "memory")
    # three simulated lanes
    dirs = {"active_a": None, "active_b": None, "stalled": None}
    for name in dirs:
        d = os.path.join(root, name)
        os.makedirs(d)
        dirs[name] = d

    def touch(lane, tag):
        p = os.path.join(dirs[lane], f"f_{tag}.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("x\n")
        # force a distinct mtime
        future = time.time() + 1.0
        os.utime(p, (future, future))

    state = os.path.join(tmp, "state.jsonl")
    sim_lanes = list(dirs)  # [active_a, active_b, stalled]
    # seed initial files
    touch("active_a", "s0"); touch("active_b", "s0"); touch("stalled", "s0")
    for i in range(4):  # 4 passes
        if i > 0:
            touch("active_a", f"p{i}")   # advances every pass
            touch("active_b", f"p{i}")   # advances every pass
            # "stalled" intentionally never touched after seed
        time.sleep(0.05)
        record_pass(state, scan_lanes(root, sim_lanes), pass_id=i)

    res = detect_stalls(state, threshold=3)
    check("stalled agent flagged", res.get("stalled", {}).get("stalled") is True)
    check("active_a not flagged", res.get("active_a", {}).get("stalled") is False)
    check("active_b not flagged", res.get("active_b", {}).get("stalled") is False)
    check("evidence has 3 identical mtimes for stalled",
          len(set(res["stalled"]["evidence"])) == 1 and len(res["stalled"]["evidence"]) == 3)

    # negative: with only 2 passes, nothing may be flagged (insufficient history)
    state2 = os.path.join(tmp, "state2.jsonl")
    for i in range(2):
        record_pass(state2, scan_lanes(root, sim_lanes), pass_id=i)
    res2 = detect_stalls(state2, threshold=3)
    check("insufficient history -> no flags", res2 == {})

    print(("SELFTEST PASS (all assertions)" if ok else "SELFTEST FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--threshold", type=int, default=3)
    a = ap.parse_args()

    if a.selftest:
        sys.exit(_selftest())
    if a.scan:
        lanes = scan_lanes(a.root)
        rec = record_pass(a.state, lanes)
        print(json.dumps({"recorded": True, "pass_id": rec["pass_id"],
                          "lanes_scanned": len(lanes)}, indent=2))
        return
    if a.check:
        res = detect_stalls(a.state, a.threshold)
        stalled = [k for k, v in res.items() if v["stalled"]]
        print(json.dumps({"threshold": a.threshold,
                          "passes_available": len(load_passes(a.state)),
                          "stalled_agents": stalled,
                          "detail": res}, indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()