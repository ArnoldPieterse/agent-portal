#!/usr/bin/env python
"""Fleet Roster Versioning (Orchestrator cycle-7 goal #10).

Snapshots agents.json at each cycle boundary to memory/orchestrator/
roster-snapshots/cycle-N.json and computes added / removed / re-roled diffs
between consecutive cycles. Single source of truth for the roster: this module
is loaded by path from agent_portal.py (/api/fleet/roster-history) so the CLI
and the endpoint can never drift.

CLI:
  python memory/orchestrator/roster_snapshot.py --snapshot [N]   # write cycle-N.json (N defaults to latest+1)
  python memory/orchestrator/roster_snapshot.py --history        # chronological list + diffs
  python memory/orchestrator/roster_snapshot.py --diff A B       # diff two cycle numbers
  python memory/orchestrator/roster_snapshot.py --self-test      # verify diff logic on fixtures
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SNAP_DIR = os.path.join(HERE, "roster-snapshots")
AGENTS_JSON = os.path.join(ROOT, "agents.json")

# Fields that matter for a roster identity diff.
CAPTURE_FIELDS = ("id", "name", "model_id", "tools")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_agents():
    """Return {name: {id, name, model_id, tools}} from the live agents.json."""
    with open(AGENTS_JSON) as f:
        data = json.load(f)
    out = {}
    for a in data.get("agents", []):
        rec = {k: a.get(k) for k in CAPTURE_FIELDS}
        # normalise tools to a sorted list so ordering noise never reads as a re-role
        rec["tools"] = sorted(a.get("tools") or [])
        out[a.get("name") or a.get("id")] = rec
    return out


def _snap_path(n):
    return os.path.join(SNAP_DIR, "cycle-%d.json" % n)


def existing_cycles():
    nums = []
    if os.path.isdir(SNAP_DIR):
        for fn in os.listdir(SNAP_DIR):
            m = re.match(r"cycle-(\d+)\.json$", fn)
            if m:
                nums.append(int(m.group(1)))
    return sorted(nums)


def load_snapshot(n):
    with open(_snap_path(n)) as f:
        return json.load(f)


def snapshot(cycle=None, agents=None):
    """Write cycle-N.json. Returns (path, payload). If cycle is None use latest+1."""
    os.makedirs(SNAP_DIR, exist_ok=True)
    if agents is None:
        agents = read_agents()
    if cycle is None:
        nums = existing_cycles()
        cycle = (nums[-1] + 1) if nums else 1
    payload = {
        "cycle": cycle,
        "timestamp": _now(),
        "source": "agents.json",
        "n_agents": len(agents),
        "agents": agents,
    }
    path = _snap_path(cycle)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path, payload


def diff(a, b):
    """Diff two {name: agent} dicts. Returns added / removed / re_roled.

    re_roled = same name present in both but model_id or tools changed."""
    a_keys = set(a)
    b_keys = set(b)
    added = sorted(b_keys - a_keys)
    removed = sorted(a_keys - b_keys)
    re_roled = []
    for name in sorted(a_keys & b_keys):
        if (a[name].get("model_id") != b[name].get("model_id")
                or a[name].get("tools") != b[name].get("tools")):
            re_roled.append({
                "name": name,
                "from_model": a[name].get("model_id"),
                "to_model": b[name].get("model_id"),
                "tools_changed": a[name].get("tools") != b[name].get("tools"),
            })
    return {"added": added, "removed": removed, "re_roled": re_roled}


def history():
    """Chronological list of snapshots with diff vs the previous cycle."""
    out = []
    prev = None
    for n in existing_cycles():
        snap = load_snapshot(n)
        agents = snap["agents"]
        entry = {
            "cycle": n,
            "timestamp": snap.get("timestamp"),
            "n_agents": snap.get("n_agents", len(agents)),
            "diff_from_prev": (None if prev is None else diff(prev, agents)),
        }
        out.append(entry)
        prev = agents
    return out


def self_test():
    """Verify the diff mechanism on two clearly-labelled fixtures (not real history).
    Returns True iff every assertion passes."""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="roster_selftest_")
    # temporarily point SNAP_DIR at the temp dir by monkeypatching the path helper
    global _snap_path, SNAP_DIR
    real_dir, real_path = SNAP_DIR, _snap_path
    SNAP_DIR = tmp
    _snap_path = lambda n: os.path.join(tmp, "cycle-%d.json" % n)
    try:
        base = {
            "Orchestrator": {"id": "orchestrator", "name": "Orchestrator", "model_id": "atlas-q8", "tools": ["terminal"]},
            "Researcher":   {"id": "researcher",   "name": "Researcher",   "model_id": "quinn-q4",  "tools": ["web_search"]},
        }
        changed = {
            "Orchestrator": {"id": "orchestrator", "name": "Orchestrator", "model_id": "atlas-q8", "tools": ["terminal"]},
            "Researcher":   {"id": "researcher",   "name": "Researcher",   "model_id": "quinn-q8",  "tools": ["web_search"]},  # re-rolled
            "Builder":      {"id": "builder",      "name": "Builder",      "model_id": "qwen-27b",  "tools": ["python"]},     # added
        }
        snapshot(cycle=6, agents=base)
        snapshot(cycle=7, agents=changed)
        d = diff(base, changed)
        assert d["added"] == ["Builder"], d
        assert d["removed"] == [], d
        assert len(d["re_roled"]) == 1 and d["re_roled"][0]["name"] == "Researcher", d
        assert d["re_roled"][0]["from_model"] == "quinn-q4" and d["re_roled"][0]["to_model"] == "quinn-q8", d
        # removed path
        back = {k: v for k, v in base.items()}
        d2 = diff(changed, back)
        assert d2["removed"] == ["Builder"] and d2["added"] == [], d2
        h = history()
        assert [e["cycle"] for e in h] == [6, 7], h
        assert h[0]["diff_from_prev"] is None, h
        assert h[1]["diff_from_prev"]["added"] == ["Builder"], h
        print("SELF-TEST PASS: diff added/removed/re_roled all correct; history chronological")
        return True
    finally:
        SNAP_DIR, _snap_path = real_dir, real_path
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    cmd = args[0]
    if cmd == "--self-test":
        ok = self_test()
        sys.exit(0 if ok else 1)
    elif cmd == "--snapshot":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        path, payload = snapshot(cycle=n)
        print("wrote %s (cycle=%d, n_agents=%d)" % (os.path.relpath(path, ROOT), payload["cycle"], payload["n_agents"]))
    elif cmd == "--history":
        print(json.dumps(history(), indent=2))
    elif cmd == "--diff":
        a, b = int(args[1]), int(args[2])
        print(json.dumps(diff(load_snapshot(a)["agents"], load_snapshot(b)["agents"]), indent=2))
    else:
        print("unknown command: %s" % cmd)
        sys.exit(2)
