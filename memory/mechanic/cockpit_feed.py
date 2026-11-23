"""Cockpit Feed Aggregator - produces a single JSON the cockpit UI reads.

Reads latest entries from fleet data sources and writes memory/ops/cockpit-feed.json.
Run manually or via schtask every 5 min.

Usage:
  python memory/mechanic/cockpit_feed.py          # write feed
  python memory/mechanic/cockpit_feed.py --check  # validate existing feed
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

OPS = Path("memory/ops")
FEED_PATH = OPS / "cockpit-feed.json"


def _last_jsonl(path: Path) -> dict | None:
    """Return the last JSON object from a .jsonl file, or None."""
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    for line in reversed(lines):
        try:
            return json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def build_feed() -> dict:
    """Aggregate all fleet data sources into one cockpit-ready structure."""
    now = datetime.now(timezone.utc).isoformat()

    # Fleet snapshot (agents, hosts, goals)
    snapshot = _last_jsonl(OPS / "fleet-snapshots.jsonl") or {}

    # Health score
    health = _last_jsonl(OPS / "health-score.jsonl") or {"score": None}

    # Active incidents (last 5)
    alerts_path = OPS / "incident-alerts.jsonl"
    alerts = []
    if alerts_path.exists():
        lines = alerts_path.read_text(encoding="utf-8").strip().split("\n")
        for line in lines[-5:]:
            try:
                alerts.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                pass

    # Decision log (last 3)
    decisions = []
    dec_path = OPS / "decision-log.jsonl"
    if dec_path.exists():
        lines = dec_path.read_text(encoding="utf-8").strip().split("\n")
        for line in lines[-3:]:
            try:
                decisions.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                pass

    # Down seats
    down_seats = _read_json(OPS / "down-seats.json") or {"seats": []}

    # Goal progress from snapshot
    goal_progress = snapshot.get("goal_progress", {})
    total_goals = sum(g.get("total", 0) for g in goal_progress.values())
    verified_goals = sum(g.get("verified", 0) for g in goal_progress.values())

    feed = {
        "ts": now,
        "health_score": health.get("score"),
        "fleet_status": "NOMINAL" if (health.get("score") or 0) >= 80 else "DEGRADED",
        "agents": snapshot.get("agent_statuses", []),
        "hosts": snapshot.get("host_resources", []),
        "goals": {
            "total": total_goals,
            "verified": verified_goals,
            "pct": round(100 * verified_goals / max(total_goals, 1), 1),
            "by_lane": goal_progress,
        },
        "down_seats": down_seats.get("seats", []),
        "active_incidents": alerts,
        "recent_decisions": decisions,
    }
    return feed


def check_feed() -> bool:
    """Validate the existing cockpit-feed.json is well-formed and fresh."""
    if not FEED_PATH.exists():
        print("FAIL: cockpit-feed.json does not exist")
        return False
    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"FAIL: cannot parse feed: {e}")
        return False

    required_keys = {"ts", "health_score", "fleet_status", "goals", "down_seats"}
    missing = required_keys - set(data.keys())
    if missing:
        print(f"FAIL: missing keys: {missing}")
        return False

    # Check freshness (warn if >10 min old)
    try:
        ts = datetime.fromisoformat(data["ts"])
        age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60
        if age_min > 10:
            print(f"WARN: feed is {age_min:.0f} min old")
        else:
            print(f"OK: feed fresh ({age_min:.1f} min old)")
    except (ValueError, TypeError):
        print("WARN: cannot parse ts field")

    print(f"  fleet_status={data['fleet_status']} health={data['health_score']} "
          f"goals={data['goals']['verified']}/{data['goals']['total']} "
          f"down_seats={len(data['down_seats'])} incidents={len(data.get('active_incidents', []))}")
    return True


def main():
    if "--check" in sys.argv:
        ok = check_feed()
        sys.exit(0 if ok else 1)

    feed = build_feed()
    FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEED_PATH.write_text(json.dumps(feed, indent=2), encoding="utf-8")
    print(f"Cockpit feed written: {FEED_PATH}")
    print(f"  status={feed['fleet_status']} health={feed['health_score']} "
          f"goals={feed['goals']['verified']}/{feed['goals']['total']} "
          f"down_seats={len(feed['down_seats'])} incidents={len(feed['active_incidents'])}")


if __name__ == "__main__":
    main()
