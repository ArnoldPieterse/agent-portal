"""Productivity Trend Archive - daily snapshots + trend queries.

Usage:
  python memory/archivist/productivity_archiver.py archive          # snapshot today
  python memory/archivist/productivity_archiver.py trend <agent> [days]  # query
  python memory/archivist/productivity_archiver.py prune            # remove >30d old
"""
import json, os, sys, glob
from datetime import datetime, timedelta
from pathlib import Path

SOURCE = Path("memory/ops/productivity-baseline.json")
ARCHIVE_DIR = Path("memory/archivist/productivity-history")
MAX_FILES = 30  # prune beyond this

def archive():
    """Copy today's snapshot into the archive dir."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        print(f"ERROR: source {SOURCE} not found")
        return 1
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    today = datetime.now().strftime("%Y-%m-%d")
    dest = ARCHIVE_DIR / f"{today}.json"
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Archived: {dest}")
    return 0

def trend(agent, days=7):
    """Return agent's rate time-series over last N days."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=days)
    series = []
    for f in sorted(ARCHIVE_DIR.glob("*.json")):
        try:
            d = datetime.strptime(f.stem, "%Y-%m-%d")
        except ValueError:
            continue
        if d < cutoff:
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        entry = data.get(agent, {})
        series.append({
            "date": f.stem,
            "rate": entry.get("rate"),
            "total_passes": entry.get("total_passes", 0),
            "productive_passes": entry.get("productive_passes", 0),
        })
    if not series:
        print(f"No data for '{agent}' in last {days} days.")
        return 1
    print(json.dumps({"agent": agent, "window_days": days, "series": series}, indent=2))
    return 0

def prune():
    """Remove archive files older than MAX_FILES (oldest first)."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(ARCHIVE_DIR.glob("*.json"))
    excess = len(files) - MAX_FILES
    removed = 0
    for f in files[:max(0, excess)]:
        f.unlink()
        removed += 1
        print(f"Pruned: {f.name}")
    print(f"Prune complete: {removed} removed, {len(files)-removed} remaining.")
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "archive"
    if cmd == "archive":
        sys.exit(archive())
    elif cmd == "trend":
        agent = sys.argv[2] if len(sys.argv) > 2 else "archivist"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        sys.exit(trend(agent, days))
    elif cmd == "prune":
        sys.exit(prune())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
