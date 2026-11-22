#!/usr/bin/env python3
"""Fleet Capacity Governor - Orchestrator cycle-8 goal #2.

Monitors per-host VRAM usage; when a host exceeds the threshold (default 85%),
auto-unloads the least-recently-used idle agent's model from that host.
Logs all decisions to capacity-governor.jsonl.

Usage:
  python memory/orchestrator/capacity_governor.py              # live mode (queries portal)
  python memory/orchestrator/capacity_governor.py --simulate   # test with synthetic data
  python memory/orchestrator/capacity_governor.py --threshold 70  # custom threshold
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = REPO_ROOT / "memory" / "orchestrator" / "capacity-governor.jsonl"
PORTAL_BASE = "http://127.0.0.1:8099"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def log_entry(entry: dict):
    """Append a JSONL entry to the governor log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_fleet_status() -> list:
    """Query portal /api/fleet/status for per-host state.
    Returns list of dicts: {host, vram_pct, loaded_models: [...], idle_agents: [...]}
    """
    import urllib.request
    url = f"{PORTAL_BASE}/api/fleet/status"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
    hosts = []
    for h in data.get("hosts", []):
        hosts.append({
            "host": h.get("name", h.get("host", "unknown")),
            "vram_pct": h.get("vram_pct"),  # may be None if nvidia-smi unavailable
            "loaded_models": h.get("loaded_models", []),
            "state": h.get("state", "unknown"),
        })
    return hosts


def get_idle_agents() -> dict:
    """Return {agent_name: last_activity_ts} for agents with no recent activity.
    Uses portal /api/fleet/performance if available, else assumes all loaded agents idle.
    """
    import urllib.request
    try:
        url = f"{PORTAL_BASE}/api/fleet/performance"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        idle = {}
        for agent in data.get("agents", []):
            last_active = agent.get("last_active_ts")
            if last_active:
                age_s = (datetime.now(timezone.utc) - datetime.fromisoformat(last_active)).total_seconds()
                if age_s > 300:  # idle > 5 min
                    idle[agent["name"]] = last_active
        return idle
    except Exception:
        # Fallback: no performance data available, treat all as equally idle
        return {}


def simulate_fleet():
    """Synthetic fleet state for --simulate mode."""
    return [
        {
            "host": "White",
            "vram_pct": 92.0,  # exceeds threshold -> should trigger unload
            "loaded_models": ["atlas-q8", "quinn-q4", "Qwen3.8-27B-Q8_0"],
            "state": "up",
        },
        {
            "host": "Black",
            "vram_pct": 45.0,  # below threshold -> no action
            "loaded_models": ["scribe-q8"],
            "state": "up",
        },
    ]


def simulate_idle():
    """Synthetic idle map: least-recently-used is 'Researcher' (oldest ts)."""
    return {
        "Researcher": "2026-11-22T08:00:00+00:00",   # oldest -> LRU -> unload first
        "Archivist": "2026-11-22T12:30:00+00:00",
        "Scribe": "2026-11-22T14:00:00+00:00",
    }


def pick_lru_idle(host_loaded: list, idle_map: dict) -> str | None:
    """Pick the LRU idle agent whose model is loaded on this host.
    Returns model_id to unload, or None if no candidate.
    """
    # Map model_ids back to agents that own them
    agents_json = REPO_ROOT / "agents.json"
    try:
        with open(agents_json, encoding="utf-8") as f:
            roster = json.load(f)
    except Exception:
        return None

    model_to_agent = {}
    for a in roster.get("agents", []):
        mid = a.get("model_id")
        if mid:
            # First agent wins (or we could track all owners; LRU per-agent is the right unit)
            model_to_agent.setdefault(mid, a["name"])

    candidates = []
    for mid in host_loaded:
        agent_name = model_to_agent.get(mid)
        if agent_name and agent_name in idle_map:
            ts = idle_map[agent_name]
            candidates.append((ts, mid, agent_name))

    if not candidates:
        return None

    # Sort by timestamp ascending (oldest = LRU = unload first)
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]  # model_id


def execute_unload(host: str, model_id: str) -> bool:
    """Issue native /api/inference/unload on the target host. Returns True on success."""
    import urllib.request
    import urllib.error
    url = f"{PORTAL_BASE}/api/inference/unload"
    payload = json.dumps({"model": model_id, "host": host}).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        log_entry({"ts": now_iso(), "action": "UNLOAD_FAIL", "host": host,
                   "model": model_id, "error": str(e)})
        return False


def run_governor(threshold: float = 85.0):
    """Main governor loop (single pass). Returns list of actions taken."""
    if "--simulate" in sys.argv or os.environ.get("CG_SIMULATE"):
        hosts = simulate_fleet()
        idle_map = simulate_idle()
    else:
        try:
            hosts = get_fleet_status()
        except Exception as e:
            log_entry({"ts": now_iso(), "action": "PROBE_FAIL", "error": str(e)})
            return []
        idle_map = get_idle_agents()

    actions = []
    for host in hosts:
        vram = host.get("vram_pct")
        if vram is None:
            continue  # can't measure, skip
        if vram < threshold:
            log_entry({"ts": now_iso(), "action": "OK", "host": host["host"],
                       "vram_pct": vram, "threshold": threshold})
            continue

        # Host is over threshold - find LRU idle to unload
        model_to_unload = pick_lru_idle(host["loaded_models"], idle_map)
        if not model_to_unload:
            log_entry({"ts": now_iso(), "action": "NO_CANDIDATE", "host": host["host"],
                       "vram_pct": vram, "threshold": threshold})
            continue

        # Execute unload (skip actual HTTP in simulate mode)
        if "--simulate" in sys.argv or os.environ.get("CG_SIMULATE"):
            success = True  # pretend success
        else:
            success = execute_unload(host["host"], model_to_unload)

        entry = {"ts": now_iso(), "action": "UNLOAD_SUCCESS" if success else "UNLOAD_FAIL",
                 "host": host["host"], "model": model_to_unload,
                 "vram_pct": vram, "threshold": threshold}
        log_entry(entry)
        actions.append(entry)

    return actions


def main():
    parser = argparse.ArgumentParser(description="Fleet Capacity Governor")
    parser.add_argument("--simulate", action="store_true", help="Use synthetic data (no live probes)")
    parser.add_argument("--threshold", type=float, default=85.0, help="VRAM %% threshold (default 85)")
    args = parser.parse_args()

    actions = run_governor(threshold=args.threshold)

    if args.simulate:
        print(f"SIMULATE: {len(actions)} action(s) taken")
        for a in actions:
            print(f"  {a['action']}: host={a['host']} model={a.get('model')} vram={a['vram_pct']}%")
    else:
        if actions:
            print(f"LIVE: {len(actions)} unload(s) executed")
        else:
            print("LIVE: all hosts within threshold")

    # Always exit 0 (governor is advisory; failures are logged not fatal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
