#!/usr/bin/env python3
"""
fleet_mode.py — Fleet Mode Controller (Orchestrator)
Determines current fleet mode from goal completion % + time-since-last-activity.
Writes to memory/ops/fleet-mode.json (SSOT read by cockpit + dispatch).

Mode logic:
  WORK:        any agent has open goals (goal_pct < 100%)
  MAINTENANCE: all reached (100%), <6h since last activity
  IDLE:        all reached (100%), >=6h since last activity

Usage:
  python memory/orchestrator/fleet_mode.py [--json] [--verbose]
"""
import json, os, re, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
GOALS_DIR = BASE / "memory" / "goals"
OPS_DIR = BASE / "memory" / "ops"
OUTPUT_FILE = OPS_DIR / "fleet-mode.json"

# Activity signals: files that indicate fleet activity (most recent mtime wins)
ACTIVITY_FILES = [
    "memory/ops/scheduler-log.jsonl",
    "memory/ops/fleet-snapshots.jsonl",
    "memory/ops/decision-log.jsonl",
    "memory/ops/autonomous-actions.jsonl",
]

# Thresholds
IDLE_THRESHOLD_HOURS = 6.0

AGENT_FILES = {
    "orchestrator": "orchestrator.md",
    "researcher":   "researcher.md",
    "builder":      "builder.md",
    "archivist":    "archivist.md",
    "scribe":       "scribe.md",
    "verifier":     "verifier.md",
    "mechanic":     "mechanic.md",
    "designer":     "designer.md",
}


def parse_goal_status(agent: str, filename: str):
    """Parse a goal file and return (total, reached)."""
    path = GOALS_DIR / filename
    if not path.exists():
        return 0, 0
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    total = 0
    reached = 0
    for line in lines:
        # Match numbered goal lines: "1. **Goal Name** ..."
        m = re.match(r'^\s*(\d+)\.\s+\*\*', line)
        if not m:
            continue
        total += 1
        # Evidence markers: (verified: ...) or (pointer: <path>)
        has_verified = "(verified:" in line or "— recorded" in line
        has_pointer = re.search(r'\(pointer:\s*([^)]+)\)', line)
        if has_verified:
            reached += 1
        elif has_pointer:
            # Pointer counts only if the leaf file exists
            ptr_path = Path(BASE / has_pointer.group(1).strip())
            if ptr_path.exists():
                reached += 1
    return total, reached


def get_goal_stats(verbose=False):
    """Get fleet-wide goal statistics."""
    per_agent = {}
    total_goals = 0
    total_reached = 0
    for agent, fname in AGENT_FILES.items():
        t, r = parse_goal_status(agent, fname)
        per_agent[agent] = {"total": t, "reached": r}
        total_goals += t
        total_reached += r
    pct = (total_reached / total_goals * 100) if total_goals > 0 else 0.0
    open_count = total_goals - total_reached
    if verbose:
        print(f"Goal stats: {total_reached}/{total_goals} ({pct:.1f}%)")
        for a, s in per_agent.items():
            print(f"  {a}: {s['reached']}/{s['total']}")
    return {
        "total": total_goals,
        "reached": total_reached,
        "open": open_count,
        "pct": round(pct, 1),
        "per_agent": per_agent,
    }


def get_last_activity_time(verbose=False):
    """Get the most recent activity timestamp from known signal files."""
    latest = None
    latest_file = None
    for rel in ACTIVITY_FILES:
        p = BASE / rel
        if p.exists():
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if latest is None or mtime > latest:
                latest = mtime
                latest_file = rel
    # Fallback: scan memory/ for most recent file modification (last 20 files by mtime)
    if latest is None:
        try:
            mem_dir = BASE / "memory"
            files = [f for f in mem_dir.rglob("*") if f.is_file()]
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            if files:
                latest = datetime.fromtimestamp(files[0].stat().st_mtime, tz=timezone.utc)
                latest_file = str(files[0].relative_to(BASE))
        except Exception:
            pass
    if verbose and latest:
        elapsed_h = (datetime.now(tz=timezone.utc) - latest).total_seconds() / 3600
        print(f"Last activity: {latest.isoformat()} ({elapsed_h:.1f}h ago, from {latest_file})")
    return latest, latest_file


def determine_mode(goal_stats, last_activity):
    """Apply mode decision logic."""
    pct = goal_stats["pct"]
    now = datetime.now(tz=timezone.utc)
    if last_activity:
        elapsed_h = (now - last_activity).total_seconds() / 3600
    else:
        elapsed_h = float('inf')

    if pct < 100.0:
        mode = "WORK"
    elif elapsed_h < IDLE_THRESHOLD_HOURS:
        mode = "MAINTENANCE"
    else:
        mode = "IDLE"
    return mode, round(elapsed_h, 2)


def atomic_write(path: Path, data: dict):
    """Write JSON atomically: write to temp in same dir + os.rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, str(path))  # atomic on POSIX; near-atomic on Windows
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    verbose = "--verbose" in sys.argv
    as_json = "--json" in sys.argv

    # 1. Get goal stats
    goal_stats = get_goal_stats(verbose)

    # 2. Get last activity time
    last_activity, source_file = get_last_activity_time(verbose)

    # 3. Determine mode
    mode, elapsed_h = determine_mode(goal_stats, last_activity)

    # 4. Build output
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    result = {
        "mode": mode,
        "timestamp": now_iso,
        "goal_pct": goal_stats["pct"],
        "goals_total": goal_stats["total"],
        "goals_reached": goal_stats["reached"],
        "goals_open": goal_stats["open"],
        "elapsed_since_activity_h": elapsed_h,
        "activity_source": source_file,
        "threshold_idle_h": IDLE_THRESHOLD_HOURS,
    }

    # 5. Atomic write
    atomic_write(OUTPUT_FILE, result)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Fleet mode: {mode}")
        print(f"  Goals: {goal_stats['reached']}/{goal_stats['total']} ({goal_stats['pct']}%)")
        print(f"  Elapsed since activity: {elapsed_h}h (source: {source_file})")
        print(f"  Written: {OUTPUT_FILE.relative_to(BASE)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
