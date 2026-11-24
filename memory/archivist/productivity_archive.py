"""Productivity Trend Archiver - archives daily snapshots of productivity-baseline.json.

Usage:
    python memory/archivist/productivity_archive.py snapshot       # take today's snapshot
    python memory/archivist/productivity_archive.py trend <agent>  # query agent's rate over last N days
    python memory/archivist/productivity_archive.py prune          # remove entries >30 days old
"""

import json
import pathlib
import sys
from datetime import datetime, timezone

HISTORY_DIR = pathlib.Path("memory/archivist/productivity-history")
BASELINE_PATH = pathlib.Path("memory/ops/productivity-baseline.json")
MAX_AGE_DAYS = 30


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def snapshot():
    """Take today's snapshot of productivity-baseline.json."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    if not BASELINE_PATH.exists():
        print(f"ERROR: {BASELINE_PATH} not found")
        sys.exit(1)

    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    out_path = HISTORY_DIR / f"{_today()}.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Snapshot written: {out_path}")
    return out_path


def trend(agent: str, days: int = 7):
    """Query agent's rate over the last N days from archived snapshots."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(HISTORY_DIR.glob("*.json"))
    # Take last `days` files
    recent = files[-days:] if len(files) >= days else files

    result = {"agent": agent, "window_days": len(recent), "series": []}
    for f in recent:
        data = json.loads(f.read_text(encoding="utf-8"))
        entry = data.get(agent, {})
        result["series"].append({
            "date": f.stem,
            "rate": entry.get("rate"),
            "total_passes": entry.get("total_passes", 0),
            "productive_passes": entry.get("productive_passes", 0),
        })

    print(json.dumps(result, indent=2))
    return result


def prune():
    """Remove snapshot files older than MAX_AGE_DAYS."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    removed = []
    for f in sorted(HISTORY_DIR.glob("*.json")):
        try:
            d = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        age_days = (now - d).days
        if age_days > MAX_AGE_DAYS:
            f.unlink()
            removed.append(f.name)

    if removed:
        print(f"Pruned {len(removed)} files: {', '.join(removed)}")
    else:
        print("Nothing to prune.")
    return removed


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    if cmd == "snapshot":
        snapshot()
    elif cmd == "trend":
        agent = sys.argv[2] if len(sys.argv) > 2 else "archivist"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        trend(agent, days)
    elif cmd == "prune":
        prune()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
