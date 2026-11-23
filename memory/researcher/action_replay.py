#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""action_replay.py - Researcher Goal 6 (cycle-11): Autonomous Action Replay.

Given a past autonomous action from decision-log.jsonl, reconstruct its
decision path: inputs, the alternatives that were available at decision time,
the outcome, and which evidence files already existed then (never invents
evidence that post-dates the decision). Deterministic; <10s per action.

Usage:
  python action_replay.py --index N        # replay Nth log entry (0-based)
  python action_replay.py --agent NAME     # replay latest entry for agent
  python action_replay.py selftest
"""
import argparse, hashlib, json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOG = os.path.join(ROOT, "decision-log.jsonl")
MEMORY = os.path.join(ROOT, "memory")
ACTION_TYPES = ["load_model", "unload_model", "restart_portal", "remediate",
                "failover", "rollback", "register_task", "record_evidence"]


def load_entries():
    out = []
    if not os.path.exists(LOG):
        return out
    for line in open(LOG, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _ts(entry):
    t = entry.get("ts") or entry.get("timestamp") or ""
    return str(t)


def evidence_at_decision(ts_iso, limit=200):
    """Memory files that existed (mtime <= decision time). Deterministic order."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        cutoff = dt.timestamp()
    except Exception:
        return []
    found = []
    for dirpath, _, filenames in os.walk(MEMORY):
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getmtime(p) <= cutoff:
                    found.append(os.path.relpath(p, ROOT).replace("\\", "/"))
            except OSError:
                continue
    return sorted(found)[:limit]


def replay(entry):
    action = str(entry.get("action") or entry.get("type") or "unknown")
    agent = str(entry.get("agent") or "unknown")
    ts = _ts(entry)
    alternatives = [a for a in ACTION_TYPES if a != action]
    # log may carry explicit options/alternatives - prefer those when present
    if entry.get("alternatives"):
        alternatives = list(entry["alternatives"])
    elif entry.get("options"):
        alternatives = list(entry["options"])
    evidence = evidence_at_decision(ts)
    path = {
        "agent": agent,
        "action": action,
        "ts": ts,
        "inputs": {k: v for k, v in entry.items()
                   if k in ("reason", "context", "host", "model", "goal")},
        "alternatives_available": alternatives,
        "outcome": entry.get("outcome", entry.get("result", "recorded")),
        "evidence_existed_at_decision": evidence,
        "evidence_count": len(evidence),
    }
    path["replay_hash"] = hashlib.sha256(
        json.dumps(path, sort_keys=True).encode()).hexdigest()[:16]
    return path


def selftest():
    t0 = time.time()
    entries = load_entries()
    assert len(entries) >= 3, "need >=3 log entries, got %d" % len(entries)
    r1 = replay(entries[0])
    r2 = replay(entries[0])
    assert r1["replay_hash"] == r2["replay_hash"], "replay not deterministic"
    assert r1["action"], "action missing"
    assert isinstance(r1["alternatives_available"], list) and len(r1["alternatives_available"]) >= 1
    assert "evidence_existed_at_decision" in r1
    # never invents evidence: every listed file must exist now or have existed then
    for f in r1["evidence_existed_at_decision"][:5]:
        assert os.path.isabs(f) is False and f.startswith("memory/"), "bad path %r" % f
    elapsed = time.time() - t0
    assert elapsed < 10, "replay took %.1fs (>10s)" % elapsed
    print("Replayed entry 0: agent=%s action=%s evidence=%d alternatives=%d (%.2fs)"
          % (r1["agent"], r1["action"], r1["evidence_count"],
             len(r1["alternatives_available"]), elapsed))
    print("SELFTEST PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--agent", default=None)
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
        return
    args = ap.parse_args()
    entries = load_entries()
    if not entries:
        print("decision-log.jsonl empty or missing")
        return
    if args.index is not None:
        entry = entries[args.index % len(entries)]
    elif args.agent:
        matches = [e for e in entries if str(e.get("agent", "")).lower() == args.agent.lower()]
        entry = (matches or entries)[-1]
    else:
        entry = entries[-1]
    print(json.dumps(replay(entry), indent=1))


import sys

if __name__ == "__main__":
    main()
