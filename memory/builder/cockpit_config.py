#!/usr/bin/env python3
"""Cockpit Self-Configuration Engine — auto-generate panel layout from fleet state.

Reads fleet state (from /api/cockpit or a JSON file), determines which panels
to show, their priority order, and density settings. Emits a config JSON that
the frontend can consume directly.

Usage:
  python memory/builder/cockpit_config.py [--state FILE] [--dry-run]

Verification (AC):
  - 3 fleet states produce different panel layouts
  - A state with active incident shows incident panel first
  - Config is valid JSON parseable by the frontend
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / "memory" / "builder"

# ─── Panel Definitions ────────────────────────────────────────────────────────

PANELS = {
    "incident": {
        "id": "incident",
        "title": "Active Incidents",
        "priority_base": 1,
        "show_when": "incidents_active",
    },
    "capacity": {
        "id": "capacity",
        "title": "Fleet Capacity",
        "priority_base": 2,
        "show_when": "vram_above_70",
    },
    "evolution": {
        "id": "evolution",
        "title": "Topology Evolution",
        "priority_base": 3,
        "show_when": "topology_changes_pending",
    },
    "health": {
        "id": "health",
        "title": "Fleet Health",
        "priority_base": 4,
        "show_when": "always",
    },
    "goals": {
        "id": "goals",
        "title": "Goal Progress",
        "priority_base": 5,
        "show_when": "always",
    },
    "loop_status": {
        "id": "loop_status",
        "title": "Autonomy Loop Status",
        "priority_base": 6,
        "show_when": "always",
    },
    "stale_alerts": {
        "id": "stale_alerts",
        "title": "Stale Data Alerts",
        "priority_base": 7,
        "show_when": "stale_data_present",
    },
}

# ─── Condition Evaluators ─────────────────────────────────────────────────────

def evaluate_conditions(fleet_state: dict) -> set:
    """Return the set of condition keys that are TRUE for this fleet state."""
    conds = set()

    # Always-on conditions
    conds.add("always")

    # Active incidents
    if fleet_state.get("active_incidents", 0) > 0:
        conds.add("incidents_active")

    # VRAM above threshold (any host)
    hosts = fleet_state.get("hosts", [])
    for h in hosts:
        vram_pct = h.get("vram_percent", 0)
        if vram_pct > 70:
            conds.add("vram_above_70")
            break

    # Topology changes pending
    if fleet_state.get("topology_changes_pending", 0) > 0:
        conds.add("topology_changes_pending")

    # Stale data present
    if fleet_state.get("stale_data_count", 0) > 0:
        conds.add("stale_data_present")

    return conds


# ─── Layout Generator ─────────────────────────────────────────────────────────

def generate_config(fleet_state: dict) -> dict:
    """Generate cockpit layout config from fleet state."""
    conditions = evaluate_conditions(fleet_state)

    # Determine which panels to show and their priority
    visible_panels = []
    for pid, pdef in PANELS.items():
        if pdef["show_when"] in conditions:
            # Priority adjustment: incident panel gets boosted to absolute first
            priority = pdef["priority_base"]
            if pid == "incident" and "incidents_active" in conditions:
                priority = 0  # absolute top
            visible_panels.append({
                "panel_id": pid,
                "title": pdef["title"],
                "priority": priority,
                "density": "compact" if "incidents_active" in conditions else "normal",
            })

    # Sort by priority
    visible_panels.sort(key=lambda p: p["priority"])

    # Density mode
    density_mode = "incident" if "incidents_active" in conditions else "calm"

    # Build output config
    now = datetime.now(timezone.utc).isoformat()
    config = {
        "schema_version": 1,
        "generated_at": now,
        "density_mode": density_mode,
        "fleet_summary": {
            "hosts_online": fleet_state.get("hosts_online", len(fleet_state.get("hosts", []))),
            "active_incidents": fleet_state.get("active_incidents", 0),
            "avg_vram_percent": _avg_vram(fleet_state),
            "goals_reached": fleet_state.get("goals_reached", 0),
        },
        "panels": visible_panels,
        "refresh_interval_s": 30 if density_mode == "incident" else 120,
    }

    return config


def _avg_vram(fleet_state: dict) -> float:
    hosts = fleet_state.get("hosts", [])
    if not hosts:
        return 0.0
    vals = [h.get("vram_percent", 0) for h in hosts]
    return round(sum(vals) / len(vals), 1)


# ─── Test States ──────────────────────────────────────────────────────────────

TEST_STATES = {
    "calm": {
        "hosts_online": 4,
        "active_incidents": 0,
        "topology_changes_pending": 0,
        "stale_data_count": 0,
        "goals_reached": 62,
        "hosts": [
            {"name": "white", "vram_percent": 35},
            {"name": "black", "vram_percent": 42},
            {"name": "pale", "vram_percent": 28},
            {"name": "gray", "vram_percent": 51},
        ],
    },
    "incident": {
        "hosts_online": 3,
        "active_incidents": 2,
        "topology_changes_pending": 1,
        "stale_data_count": 1,
        "goals_reached": 60,
        "hosts": [
            {"name": "white", "vram_percent": 85},
            {"name": "black", "vram_percent": 78},
            {"name": "pale", "vram_percent": 92},
            {"name": "gray", "vram_percent": 0},
        ],
    },
    "degraded": {
        "hosts_online": 4,
        "active_incidents": 0,
        "topology_changes_pending": 3,
        "stale_data_count": 4,
        "goals_reached": 58,
        "hosts": [
            {"name": "white", "vram_percent": 72},
            {"name": "black", "vram_percent": 65},
            {"name": "pale", "vram_percent": 68},
            {"name": "gray", "vram_percent": 71},
        ],
    },
}


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Cockpit Self-Configuration Engine")
    ap.add_argument("--state", type=str, help="Path to fleet state JSON file")
    ap.add_argument("--dry-run", action="store_true", help="Print config without writing")
    ap.add_argument("--selftest", action="store_true", help="Run verification tests")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(run_selftest())

    # Load fleet state
    if args.state:
        with open(args.state) as f:
            fleet_state = json.load(f)
    else:
        # Try to read from cockpit-data.json if it exists
        cd = ROOT / "memory" / "builder" / "cockpit-data.json"
        if cd.exists():
            fleet_state = json.loads(cd.read_text(encoding="utf-8"))
        else:
            print("No state file provided and no cockpit-data.json found. Using calm defaults.")
            fleet_state = TEST_STATES["calm"]

    config = generate_config(fleet_state)

    if args.dry_run:
        print(json.dumps(config, indent=2))
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_path = OUTPUT_DIR / f"cockpit-config-{date_str}.json"
        out_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")


def run_selftest() -> int:
    """Verify ACs: 3 different layouts, incident-first ordering, valid JSON."""
    results = []

    # Generate configs for all 3 test states
    configs = {}
    for name, state in TEST_STATES.items():
        cfg = generate_config(state)
        configs[name] = cfg

    # AC1: 3 fleet states produce different panel layouts
    calm_panels = [p["panel_id"] for p in configs["calm"]["panels"]]
    incident_panels = [p["panel_id"] for p in configs["incident"]["panels"]]
    degraded_panels = [p["panel_id"] for p in configs["degraded"]["panels"]]

    distinct = len({tuple(calm_panels), tuple(incident_panels), tuple(degraded_panels)}) == 3
    results.append(("3 states -> 3 distinct layouts", distinct,
                    f"calm={calm_panels}, incident={incident_panels}, degraded={degraded_panels}"))

    # AC2: Incident state shows incident panel first
    incident_first = incident_panels[0] == "incident" if incident_panels else False
    results.append(("Incident state -> incident panel first", incident_first,
                    f"first={incident_panels[0] if incident_panels else 'N/A'}"))

    # AC3: Config is valid JSON (round-trip)
    for name, cfg in configs.items():
        serialized = json.dumps(cfg)
        deserialized = json.loads(serialized)
        ok = deserialized == cfg
        results.append((f"JSON round-trip: {name}", ok, ""))

    # AC4: Density mode correct
    calm_mode = configs["calm"]["density_mode"] == "calm"
    incident_mode = configs["incident"]["density_mode"] == "incident"
    results.append(("Density modes correct", calm_mode and incident_mode,
                    f"calm={configs['calm']['density_mode']}, incident={configs['incident']['density_mode']}"))

    # Report
    print("\n=== Cockpit Config Self-Test ===")
    all_pass = True
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        line = f"[{status}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)

    print(f"\n{'ALL PASS' if all_pass else 'SOME FAILED'} ({sum(1 for _,p,_ in results if p)}/{len(results)})")
    return 0 if all_pass else 1


if __name__ == "__main__":
    main()
