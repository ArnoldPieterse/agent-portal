#!/usr/bin/env python3
"""Auto-Loop Pass Logger (Builder goal 4, cycle 15).

Log every auto-loop pass to memory/ops/autoloop.jsonl with fields:
timestamp, agent, task_type (WORK/MAINT/IDLE), task_text, productive (bool),
duration_ms. productive = actual file-change detection under memory/ since the
agent's previous touch (mtime scan, depth-limited).

Wired into agent_portal.autoloop_touch() so every completed turn is logged.
Usage: python memory/builder/autoloop_logger.py --selftest | --tail [N]
"""
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
LOG = BASE / "memory" / "ops" / "autoloop.jsonl"
FLEET_MODE = BASE / "memory" / "ops" / "fleet-mode.json"
MEMORY_DIR = BASE / "memory"
_last_touch = {}          # agent -> epoch of previous pass (in-process)


def _fleet_task_type():
    try:
        d = json.loads(FLEET_MODE.read_text(encoding="utf-8"))
        mode = str(d.get("mode", "")).upper()
        if "MAINT" in mode: return "MAINT"
        if "IDLE" in mode: return "IDLE"
        if "WORK" in mode: return "WORK"
    except Exception:
        pass
    return "WORK"


def detect_productive(since_ts, max_files=4000):
    """True if any file under memory/ changed at/after since_ts."""
    try:
        n = 0
        for root, dirs, files in os.walk(MEMORY_DIR):
            dirs[:] = [d for d in dirs if d not in (".git", "archive")]
            for f in files:
                p = os.path.join(root, f)
                if os.path.abspath(p) == os.path.abspath(str(LOG)):
                    continue  # never count the log file's own writes
                try:
                    if os.path.getmtime(p) >= since_ts:
                        return True
                except OSError:
                    pass
                n += 1
                if n >= max_files:
                    return False
        return False
    except Exception:
        return False


def log_pass(agent, task_text="", productive=None, duration_ms=None):
    """Append one pass record. Returns the record dict."""
    now = time.time()
    since = _last_touch.get(agent, now - 3600)
    if productive is None:
        productive = detect_productive(since)
    rec = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "task_type": _fleet_task_type(),
        "task_text": (task_text or "")[:200],
        "productive": bool(productive),
        "duration_ms": int(duration_ms) if duration_ms else int((now - since) * 1000),
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    _last_touch[agent] = now
    return rec


def tail(n=10):
    if not LOG.exists():
        return []
    lines = LOG.read_text(encoding="utf-8").splitlines()[-n:]
    out = []
    for l in lines:
        try: out.append(json.loads(l))
        except Exception: pass
    return out


def selftest():
    """Exercise logging + productive detection against a temp tree."""
    import tempfile
    global LOG, MEMORY_DIR
    td = Path(tempfile.mkdtemp())
    old_log, old_mem = LOG, MEMORY_DIR
    LOG = td / "autoloop.jsonl"
    MEMORY_DIR = td
    ok = fail = 0
    def check(name, cond):
        nonlocal ok, fail
        print(("  PASS: " if cond else "  FAIL: ") + name)
        if cond: ok += 1
        else: fail += 1
    try:
        (td / "a.txt").write_text("x")
        time.sleep(0.05)
        r = log_pass("t_agent", "test pass")
        check("record has all fields", all(k in r for k in ("timestamp","agent","task_type","task_text","productive","duration_ms")))
        check("file changed -> productive True", r["productive"] is True)
        time.sleep(0.1)
        r2 = log_pass("t_agent", "no change pass")
        check("no change since touch -> productive False", r2["productive"] is False)
        check("jsonl has 2 lines", len(LOG.read_text().splitlines()) == 2)
        check("tail returns records", len(tail(5)) == 2)
    finally:
        LOG, MEMORY_DIR = old_log, old_mem
    print("Result: %d/%d passed" % (ok, ok+fail))
    return fail == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import sys as _s
        _s.exit(0 if selftest() else 1)
    elif "--tail" in sys.argv:
        n = 10
        i = sys.argv.index("--tail")
        if i + 1 < len(sys.argv): n = int(sys.argv[i+1])
        for r in tail(n): print(json.dumps(r))
