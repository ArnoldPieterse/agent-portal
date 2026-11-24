"""Cycle Efficiency Index
Composite metric per cycle: (goals_completed / passes_used) * (1 - rework_rate) * (1 - idle_fraction)
Tracks trend; flags cycles where efficiency drops >20% vs 3-cycle rolling mean.

Output: memory/ops/cycle-efficiency-index.jsonl (appends), prints summary.
"""
import json, math, pathlib, sys
from datetime import datetime, timezone

OPS = pathlib.Path("memory/ops")
OUT = OPS / "cycle-efficiency-index.jsonl"

def load_jsonl(path):
    if not path.exists(): return []
    records = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if line:
            try: records.append(json.loads(line))
            except: pass
    return records

def load_json(path, default=None):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except: return default

def collect_cycle_efficiency_data():
    """Gather per-cycle efficiency components from all available sources."""
    cycles = {}
    
    # Source 1: cycle-efficiency-index.jsonl (pre-computed)
    for rec in load_jsonl(OUT):
        c = rec.get("cycle")
        if c and isinstance(c, int):
            cycles[c] = {
                "goals_completed": rec.get("goals_completed"),
                "passes_used": rec.get("passes_used"),
                "velocity_goals_per_pass": rec.get("velocity_goals_per_pass"),
                "rework_rate": rec.get("rework_rate"),
                "idle_fraction": rec.get("idle_fraction"),
                "efficiency_index": rec.get("efficiency_index"),
                "duration_hours": rec.get("duration_hours"),
                "sources": rec.get("sources", {}),
            }
    
    # Source 2: cycle-efficiency.json (latest single-cycle)
    ce = load_json(OPS / "cycle-efficiency.json")
    if ce and isinstance(ce, dict) and "cycle" in ce:
        c = ce["cycle"]
        if not isinstance(c, int): 
            try: c = int(c)
            except: pass
        if c:
            existing = cycles.get(c, {})
            existing.setdefault("goals_completed", ce.get("goals_completed"))
            existing.setdefault("passes_used", ce.get("passes_used"))
            existing.setdefault("velocity_goals_per_pass", ce.get("velocity_goals_per_pass"))
            cycles[c] = existing
    
    # Source 3: autonomy-score.json for rework_rate (only fill gaps)
    as_data = load_json(OPS / "autonomy-score.json")
    if as_data and "components" in as_data:
        rework_score = as_data["components"].get("rework_score")
        if rework_score is not None:
            # rework_rate = 1 - rework_score/100 (derived from autonomy components)
            rework_rate = round(1.0 - rework_score / 100.0, 4)
            max_cycle = max(cycles.keys()) if cycles else 0
            cycles.setdefault(max_cycle, {})
            if "rework_rate" not in cycles[max_cycle]:
                cycles[max_cycle]["rework_rate"] = rework_rate
    
    # Source 4: idle data from cycle-efficiency-N.json files (ONLY fill gaps)
    import re as _re
    for f in sorted(OPS.glob("cycle-efficiency-*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(d, dict) and "cycle" in d:
                c = d["cycle"]
                if not isinstance(c, int):
                    try: c = int(c)
                    except: continue
                cycles.setdefault(c, {})
                # idle_fraction from wasted passes - ONLY if not already set
                if "idle_fraction" not in cycles[c]:
                    total = d.get("total_passes", 0)
                    wasted = d.get("wasted_pass_count", 0)
                    if total > 1:  # only use if window covers full cycle (total>1)
                        cycles[c]["idle_fraction"] = round(wasted / total, 4)
        except:
            pass
    
    return cycles

def compute_efficiency(data):
    """Compute composite efficiency index from components. Returns None if key data missing."""
    gc = data.get("goals_completed")
    pu = data.get("passes_used")
    rr = data.get("rework_rate", 0)
    idle = data.get("idle_fraction", 0)
    
    if gc is None or pu is None or pu == 0:
        return None
    
    velocity = gc / pu
    efficiency = velocity * (1 - rr) * (1 - idle)
    return round(efficiency, 4)

def main():
    cycles = collect_cycle_efficiency_data()
    if not cycles:
        print("ERROR: No cycle efficiency data found")
        sys.exit(1)
    
    sorted_cycles = sorted(cycles.keys())
    results = []
    
    for c in sorted_cycles:
        d = cycles[c]
        # Priority: use pre-computed value if available (it was validated at write time)
        eff = d.get("efficiency_index")
        if eff is None:
            eff = compute_efficiency(d)
        
        missing = []
        if d.get("goals_completed") is None: missing.append("goals_completed")
        if d.get("passes_used") is None: missing.append("passes_used")
        if d.get("rework_rate") is None: missing.append("rework_rate")
        if d.get("idle_fraction") is None: missing.append("idle_fraction")
        
        results.append({
            "cycle": c,
            "efficiency_index": eff,
            "goals_completed": d.get("goals_completed"),
            "passes_used": d.get("passes_used"),
            "rework_rate": d.get("rework_rate"),
            "idle_fraction": d.get("idle_fraction"),
            "data_gaps": missing,
        })
    
    # Trend analysis: flag cycles where efficiency drops >20% vs 3-cycle rolling mean
    for i, r in enumerate(results):
        if r["efficiency_index"] is None:
            r["anomaly"] = None
            continue
        # Get up to 3 prior cycles with known efficiency
        prior = [x["efficiency_index"] for x in results[:i] 
                 if x["efficiency_index"] is not None][-3:]
        if len(prior) >= 2:
            mean_prior = sum(prior) / len(prior)
            if mean_prior > 0:
                drop_pct = (mean_prior - r["efficiency_index"]) / mean_prior * 100
                r["anomaly"] = {
                    "drop_vs_3cycle_mean_pct": round(drop_pct, 1),
                    "flagged": drop_pct > 20.0,
                    "prior_mean": round(mean_prior, 4),
                }
        else:
            r["anomaly"] = {"note": f"insufficient prior data ({len(prior)} points)"}
    
    # Write output (append new records, skip already-recorded cycles)
    existing_cycles = set()
    for rec in load_jsonl(OUT):
        if "cycle" in rec:
            try: existing_cycles.add(int(rec["cycle"]))
            except: pass
    
    new_records = [r for r in results if r["cycle"] not in existing_cycles]
    
    if new_records:
        with open(OUT, "a", encoding="utf-8") as f:
            for r in new_records:
                f.write(json.dumps(r) + "\n")
        print(f"Appended {len(new_records)} new record(s) to {OUT}")
    else:
        print(f"No new records (all {len(results)} cycles already recorded)")
    
    # Print summary
    print(f"\n=== Cycle Efficiency Index ===")
    print(f"Cycles with data: {len(results)} ({sorted_cycles})")
    for r in results:
        eff = r["efficiency_index"] if r["efficiency_index"] is not None else "N/A"
        gaps = f" [gaps: {','.join(r['data_gaps'])}]" if r["data_gaps"] else ""
        anomaly_str = ""
        if r.get("anomaly") and isinstance(r["anomaly"], dict):
            if r["anomaly"].get("flagged"):
                anomaly_str = f" *** ANOMALY: -{r['anomaly']['drop_vs_3cycle_mean_pct']}% vs 3-cycle mean ***"
            elif "note" in r["anomaly"]:
                pass  # skip insufficient data notes
        print(f"  cycle {r['cycle']}: efficiency={eff}{gaps}{anomaly_str}")
    
    # Data quality summary
    complete = sum(1 for r in results if not r["data_gaps"])
    print(f"\nData completeness: {complete}/{len(results)} cycles have all components")
    if complete < 3:
        print("WARNING: Need >=3 complete cycles for meaningful trend analysis")

if __name__ == "__main__":
    main()
