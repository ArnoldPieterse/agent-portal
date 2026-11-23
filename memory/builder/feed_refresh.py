"""feed_refresh.py - Regenerates memory/ops/cockpit-feed.json from local data sources.

Fixes the identified gap: cockpit-feed.json was stale (all nulls, unknown statuses,
fleet_pct: None) because it required network egress to /api/goals which is blocked
by sandbox firewall (WinError 10013).

Instead, this script computes everything from local files:
  - Host metrics: memory/ops/fleet-metrics.jsonl (latest record)
  - Goal progress: memory/goals/*.md (parse verified vs total)
  - Agent status: agents.json model mappings + fleet-metrics agents_detail

Usage: python memory/builder/feed_refresh.py [--dry-run]
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
FEED_PATH = ROOT / "memory" / "ops" / "cockpit-feed.json"
METRICS_PATH = ROOT / "memory" / "ops" / "fleet-metrics.jsonl"
GOALS_DIR = ROOT / "memory" / "goals"
AGENTS_JSON = ROOT / "agents.json"


def latest_metrics() -> dict:
    """Read the most recent record from fleet-metrics.jsonl."""
    if not METRICS_PATH.exists():
        return {}
    lines = METRICS_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return {}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {}


# Primary lane goal files (the ones that count toward fleet completion)
LANE_NAMES = ["orchestrator", "researcher", "builder", "verifier",
              "designer", "archivist", "scribe", "mechanic"]


def compute_fleet_pct() -> dict:
    """Parse goal files to compute per-lane and overall completion.
    Only primary lane files (builder.md, researcher.md, etc.) count toward fleet_pct.
    Forecast/proposal/INDEX files are listed in detail but excluded from headline pct.
    """
    lanes = {}
    total_goals = 0
    total_verified = 0
    for p in sorted(GOALS_DIR.glob("*.md")):
        if p.name.startswith("_") or "archive" in str(p) or p.stem == "INDEX":
            continue
        text = p.read_text(encoding="utf-8")
        # Count goal items (lines starting with "- [ ]" or numbered goals)
        open_items = len(re.findall(r"^- \[ \]", text, re.MULTILINE))
        verified_count = text.count("(verified:")
        total = max(open_items + verified_count, 1)  # at least 1 to avoid div0
        lanes[p.stem] = {
            "total": total,
            "verified": verified_count,
            "pct": round(verified_count / total * 100, 1) if total else 0.0,
        }
        # Only primary lane files count toward fleet_pct
        if p.stem in LANE_NAMES:
            total_goals += total
            total_verified += verified_count

    fleet_pct = round(total_verified / total_goals * 100, 1) if total_goals else 0.0
    return {"fleet_pct": fleet_pct, "lanes": lanes, "total_goals": total_goals, "total_verified": total_verified}


def agent_statuses(metrics: dict) -> list:
    """Derive agent status from latest metrics + agents.json."""
    # Try to load agents.json for model mapping
    agents_cfg = {}
    if AGENTS_JSON.exists():
        try:
            agents_cfg = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    detail = metrics.get("agents_detail", [])
    # Fallback: use known agent list from the feed itself or agents.json
    known_agents = [a.get("id") for a in agents_cfg] if isinstance(agents_cfg, list) else []
    if not known_agents:
        known_agents = ["orchestrator", "researcher", "builder", "verifier",
                        "designer", "archivist", "scribe", "mechanic"]

    # Map from metrics detail if available
    detail_map = {d.get("name"): d for d in detail}

    agents = []
    for aid in known_agents:
        d = detail_map.get(aid, {})
        status = d.get("status", "unknown")
        # If metrics show active agents > 0 and this agent isn't marked inactive, assume active
        if not metrics.get("agents_active"):
            status = "idle"
        agents.append({"id": aid, "name": aid.capitalize(), "status": status})
    return agents


def host_statuses(metrics: dict) -> list:
    """Extract per-host metrics from latest record."""
    hosts = metrics.get("hosts", [])
    if not hosts:
        # Fallback: single-host record
        return [{"host": metrics.get("host", "Unknown"),
                 "vram_pct": metrics.get("gpu_usage_pct"),
                 "cpu_pct": metrics.get("cpu_load_pct"),
                 "temp_c": metrics.get("temp_celsius")}]
    return [{"host": h.get("name", "?"),
             "vram_pct": h.get("vram_pct"),
             "cpu_pct": h.get("cpu_pct"),
             "temp_c": h.get("temp_c")} for h in hosts]


def health_score(metrics: dict) -> int:
    """Simple heuristic: start at 100, deduct for offline hosts and low goal pct."""
    score = 100
    hosts = metrics.get("hosts", [])
    if hosts:
        offline = sum(1 for h in hosts if h.get("vram_pct") is None)
        score -= offline * 5
    gp = metrics.get("goal_progress_pct", 0)
    if gp < 50:
        score -= 20
    elif gp < 80:
        score -= 10
    return max(0, min(100, score))


def build_feed(dry_run: bool = False) -> dict:
    metrics = latest_metrics()
    goals = compute_fleet_pct()
    feed = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "health_score": health_score(metrics),
        "fleet_status": "NOMINAL" if health_score(metrics) >= 80 else "DEGRADED",
        "agents": agent_statuses(metrics),
        "hosts": host_statuses(metrics),
        "goals": goals,
        "open_blockers": metrics.get("open_blockers", 0),
        "source": "feed_refresh.py (local-only, no network)",
    }
    if dry_run:
        print(json.dumps(feed, indent=2))
    else:
        FEED_PATH.write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] Wrote {FEED_PATH.relative_to(ROOT)} ({len(json.dumps(feed))} bytes)")
        print(f"  fleet_pct={goals['fleet_pct']}% health={feed['health_score']} "
              f"hosts={len(feed['hosts'])} agents={len(feed['agents'])}")
    return feed


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    build_feed(dry_run=dry)
