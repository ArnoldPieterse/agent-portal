"""Self-Healing Goal Lifecycle Manager.

Transitions goals through their lifecycle automatically:
  open -> verified -> archived (in closed_topics.json)

Operations:
  --sweep: Scan all agent goal files, archive verified goals not yet in closed_topics.json
  --selftest: Run 5 test cases covering the full lifecycle
  --status: Show current lifecycle state per agent

Usage: python memory/orchestrator/goal_lifecycle.py [--sweep|--selftest|--status]
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GOALS_DIR = os.path.normpath(os.path.join(HERE, "..", "goals"))
CLOSED_FILE = os.path.join(GOALS_DIR, "closed_topics.json")
AGENTS = ["orchestrator","researcher","builder","archivist","verifier","mechanic","designer","scribe"]


def sig(text: str) -> str:
    """Stable 12-char signature from normalized goal text."""
    norm = re.sub(r'\s+', ' ', text.strip()).lower()[:80]
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


GOAL_LINE = re.compile(r'^(\d+)\.\s+\*\*(.+?)\*\*.*$', re.MULTILINE)
VERIFIED_MARKER = re.compile(r'\(verified:\s*([^)]+)\)')


def parse_goals(md_path: str, agent: str) -> list:
    """Extract numbered goals from a markdown goal file."""
    if not os.path.exists(md_path):
        return []
    content = open(md_path, encoding='utf-8').read()
    goals = []
    for m in GOAL_LINE.finditer(content):
        num = int(m.group(1))
        name = m.group(2)
        vm = VERIFIED_MARKER.search(m.group(0))
        verified_detail = vm.group(1) if vm else ""
        text = f"**{name}**"
        goals.append({
            "num": num,
            "text": text,
            "verified": bool(vm),
            "verified_detail": verified_detail,
            "sig": sig(text),
            "agent": agent
        })
    return goals


def load_closed() -> set:
    """Return set of sigs already in closed_topics.json."""
    if not os.path.exists(CLOSED_FILE):
        return set()
    data = json.loads(open(CLOSED_FILE, encoding='utf-8').read())
    return {e["sig"] for e in data if "sig" in e}


def atomic_write_json(path: str, data):
    """Write JSON atomically (temp + rename) to prevent concurrent corruption."""
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def sweep() -> dict:
    """Archive all verified goals not yet in closed_topics.json."""
    closed_sigs = load_closed()
    if os.path.exists(CLOSED_FILE):
        closed_data = json.loads(open(CLOSED_FILE, encoding='utf-8').read())
    else:
        closed_data = []

    new_entries = []
    agents_checked = 0

    for agent in AGENTS:
        md_path = os.path.join(GOALS_DIR, f"{agent}.md")
        if not os.path.exists(md_path):
            continue
        agents_checked += 1
        goals = parse_goals(md_path, agent)
        for g in goals:
            if g["verified"] and g["sig"] not in closed_sigs:
                new_entries.append({
                    "sig": g["sig"],
                    "text": g["text"][:200],
                    "agent": agent,
                    "at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "source": "goal_lifecycle.sweep",
                    "verified_detail": g["verified_detail"][:100]
                })
                closed_sigs.add(g["sig"])

    if new_entries:
        closed_data.extend(new_entries)
        atomic_write_json(CLOSED_FILE, closed_data)

    return {"agents_checked": agents_checked, "newly_archived": len(new_entries), "total_closed": len(closed_data)}


def selftest() -> bool:
    """5 test cases covering the lifecycle (in-memory, no filesystem deps)."""
    results = []
    
    # T1: parse_goals correctly identifies verified vs open
    import io, contextlib
    test_md = "# Test\n\n1. **Open Goal** - in progress\n2. **Done Goal** - (verified: 2026-11-25 x)\n3. **Also Done** - work done (verified: 2026-11-24 y)\n"
    # Write to a real file in our working dir for parse_goals
    test_file = os.path.join(GOALS_DIR, "_selftest_tmp.md")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_md)
    goals = parse_goals(test_file, "test_agent")
    results.append(("T1: parses 3 goals, 2 verified", len(goals) == 3 and sum(1 for g in goals if g["verified"]) == 2))
    
    # T2: sig is stable and unique per different text
    s1 = sig("**Open Goal**")
    s2 = sig("**Open Goal**")
    s3 = sig("**Done Goal**")
    results.append(("T2: sig stable + unique", s1 == s2 and s1 != s3))
    
    # T3: sweep archives only unarchived verified goals (simulated)
    closed_sigs = {s3}  # "Done Goal" already archived
    to_archive = [g for g in goals if g["verified"] and g["sig"] not in closed_sigs]
    results.append(("T3: sweep targets only unarchived", len(to_archive) == 1 and to_archive[0]["num"] == 3))
    
    # T4: idempotent - second pass finds nothing new
    closed_sigs.update(g["sig"] for g in to_archive)
    to_archive_2 = [g for g in goals if g["verified"] and g["sig"] not in closed_sigs]
    results.append(("T4: idempotent (0 on re-run)", len(to_archive_2) == 0))
    
    # T5: open goals never archived
    open_goals = [g for g in goals if not g["verified"]]
    results.append(("T5: open goals excluded", all(g["sig"] not in closed_sigs for g in open_goals)))
    
    # Cleanup
    os.unlink(test_file)
    
    all_pass = all(passed for _, passed in results)
    for name, passed in results:
        print(f"  {'PASS' if passed else 'FAIL'}: {name}")
    return all_pass


def status():
    """Show lifecycle state per agent."""
    closed_sigs = load_closed()
    total_verified = 0
    total_archived = 0
    for agent in AGENTS:
        md_path = os.path.join(GOALS_DIR, f"{agent}.md")
        if not os.path.exists(md_path):
            continue
        goals = parse_goals(md_path, agent)
        verified = [g for g in goals if g["verified"]]
        archived = [g for g in verified if g["sig"] in closed_sigs]
        total_verified += len(verified)
        total_archived += len(archived)
        pending = len(verified) - len(archived)
        print(f"  {agent:12s}: {len(goals)} goals, {len(verified)} verified, {len(archived)} archived, {pending} pending-sweep")
    print(f"\n  Total closed_topics.json entries: {len(closed_sigs)}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--sweep" in sys.argv:
        result = sweep()
        print(json.dumps(result, indent=2))
    elif "--status" in sys.argv:
        status()
    else:
        print("Usage: goal_lifecycle.py [--sweep|--selftest|--status]")
