"""Cycle Cost Tracker (Orchestrator cycle-7 goal #9).

Computes per-cycle compute cost estimate from hotload-log.jsonl:
  cost_units = vram_gb × load_time_s × frequency (loads in that cycle)

Usage: python memory/orchestrator/cost_tracker.py  (prints JSON summary)
API:   GET /api/fleet/cost  (wired in agent_portal.py)
"""
import json, os, re
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # project root

HOTLOAD_LOG = os.path.join(ROOT, "memory", "llm", "hotload-log.jsonl")
CATALOG = os.path.join(ROOT, "memory", "llm", "hotload-catalog.json")


def _load_catalog():
    """Return {model_id: vram_gb} from hotload-catalog.json."""
    try:
        with open(CATALOG) as f:
            data = json.load(f)
        models = data.get("models", [])
        return {m["id"]: m.get("vram_gb", 0) for m in models}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_log():
    """Return list of hotload log entries."""
    try:
        with open(HOTLOAD_LOG) as f:
            return [json.loads(line) for line in f if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _extract_load_seconds(detail: str) -> float:
    """Parse load time from detail field (e.g. '0.0s' or '12.3s')."""
    m = re.search(r'(\d+\.?\d*)\s*s', detail)
    return float(m.group(1)) if m else 0.0


def _cycle_label(ts: str) -> str:
    """Map a timestamp to a cycle label based on date.
    Cycles are roughly weekly; we bucket by ISO week for now."""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    except (ValueError, AttributeError):
        return "unknown"


def compute_costs() -> dict:
    """Main entry point. Returns:
    {
      "total_loads": int,
      "cumulative_cost_units": float,  # sum of vram_gb * load_time_s
      "by_cycle": {cycle_label: {loads, cost_units}},
      "by_model": {model_id: {loads, avg_vram_gb, total_cost_units}},
      "entries_analyzed": int
    }
    """
    catalog = _load_catalog()
    log = _load_log()

    loads = [e for e in log if e.get("event") == "LOAD_SUCCESS"]

    by_cycle = defaultdict(lambda: {"loads": 0, "cost_units": 0.0})
    by_model = defaultdict(lambda: {"loads": 0, "vram_total": 0.0, "cost_sum": 0.0})
    cumulative = 0.0

    for e in loads:
        model = e.get("model", "unknown")
        vram = catalog.get(model, 0)
        load_s = _extract_load_seconds(e.get("detail", ""))
        cost = vram * load_s  # GB·s units
        cumulative += cost

        cycle = _cycle_label(e.get("ts", ""))
        by_cycle[cycle]["loads"] += 1
        by_cycle[cycle]["cost_units"] += cost

        by_model[model]["loads"] += 1
        by_model[model]["vram_total"] += vram
        by_model[model]["cost_sum"] += cost

    # Finalize per-model averages
    for m in by_model:
        d = by_model[m]
        d["avg_vram_gb"] = round(d["vram_total"] / max(d["loads"], 1), 2)
        del d["vram_total"]

    return {
        "total_loads": len(loads),
        "cumulative_cost_units": round(cumulative, 4),
        "by_cycle": {k: {"loads": v["loads"], "cost_units": round(v["cost_units"], 4)} for k, v in sorted(by_cycle.items())},
        "by_model": {k: {"loads": v["loads"], "avg_vram_gb": v["avg_vram_gb"], "total_cost_units": round(v["cost_sum"], 4)} for k, v in by_model.items()},
        "entries_analyzed": len(log),
    }


if __name__ == "__main__":
    print(json.dumps(compute_costs(), indent=2))