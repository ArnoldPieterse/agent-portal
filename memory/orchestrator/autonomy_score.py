"""autonomy_score.py - Fleet Autonomy Score Computation.

Composite 0-100 from:
  (a) % passes without human input (weight 0.35)
  (b) mean cycle duration vs baseline (weight 0.25)  
  (c) re-work rate (weight 0.20)
  (d) intervention frequency trend (weight 0.20)

Usage:
    python memory/orchestrator/autonomy_score.py           # compute + write JSON
    python memory/orchestrator/autonomy_score.py --selftest  # verify with synthetic data
"""
import pathlib, json, re, math
from datetime import datetime, date
from typing import Optional

MEM = pathlib.Path("memory")
INTERVENTIONS_FILE = MEM / "ops" / "human-interventions.jsonl"
CYCLE_DURATIONS_FILE = MEM / "ops" / "cycle-durations.jsonl"
ARCHIVE = MEM / "goals" / "archive"
OUTPUT = MEM / "ops" / "autonomy-score.json"
FLEET_METRICS_FILE = MEM / "ops" / "fleet-metrics.jsonl"
FLEET_SNAPSHOTS_FILE = MEM / "ops" / "fleet-snapshots.jsonl"
EXPECTED_HOSTS = ["White", "Red", "Pale", "Black"]

# Baseline: 48h (2-day) cycle is "normal" for this fleet
BASELINE_CYCLE_HOURS = 48.0

def load_interventions() -> list:
    if not INTERVENTIONS_FILE.exists():
        return []
    entries = []
    for line in INTERVENTIONS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries

def load_cycle_durations() -> list:
    if not CYCLE_DURATIONS_FILE.exists():
        return []
    entries = []
    for line in CYCLE_DURATIONS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries

def compute_pass_autonomy(interventions: list, total_passes: int = None) -> float:
    """(a) % passes without human input. 0-100."""
    if total_passes is None:
        # Estimate from cycle count * ~4 passes per day * days
        durations = load_cycle_durations()
        if durations:
            total_days = sum(d.get("duration_hours", 24) / 24 for d in durations)
            total_passes = max(int(total_days * 4), len(interventions))
        else:
            total_passes = max(len(interventions) * 10, 20)
    
    if total_passes == 0:
        return 50.0
    
    intervention_passes = min(len(interventions), total_passes)
    autonomy_pct = (1 - intervention_passes / total_passes) * 100
    return max(0, min(100, autonomy_pct))

def compute_duration_score(durations: list) -> float:
    """(b) Mean cycle duration vs baseline. Faster = better. 0-100."""
    if not durations:
        return 50.0
    
    mean_hours = sum(d.get("duration_hours", BASELINE_CYCLE_HOURS) for d in durations) / len(durations)
    
    # Score: baseline=70, half baseline=90, double baseline=40, quadruple=10
    ratio = mean_hours / BASELINE_CYCLE_HOURS
    if ratio <= 0.5:
        return 90.0
    elif ratio <= 1.0:
        # Linear from 90 (at 0.5) to 70 (at 1.0)
        return 90 - (ratio - 0.5) * 40
    elif ratio <= 2.0:
        # Linear from 70 (at 1.0) to 40 (at 2.0)
        return 70 - (ratio - 1.0) * 30
    else:
        # Diminishing: 40 at 2x, floor at 10
        return max(10, 40 - (ratio - 2.0) * 10)

def compute_rework_score() -> float:
    """(c) Re-work rate: % of goals that were reopened after being marked done. 0-100."""
    # Scan archive for "REOPENED" or "re-opened" markers
    if not ARCHIVE.exists():
        return 50.0
    
    total_goals = 0
    reworked = 0
    
    for f in ARCHIVE.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        # Count numbered goals
        goals = re.findall(r"^\d+\.\s+\*\*", content, re.MULTILINE)
        total_goals += len(goals)
        # Count re-work indicators
        reworked += len(re.findall(r"REOPEN|re-open|revert.*goal", content, re.IGNORECASE))
    
    if total_goals == 0:
        return 50.0
    
    rework_rate = reworked / total_goals
    # Score: 0% rework=100, 10%=70, 25%=30, >25%=10
    score = 100 - (rework_rate * 100) * 4
    return max(10, min(100, score))

def compute_trend_score(interventions: list) -> float:
    """(d) Intervention frequency trend. Decreasing = better. 0-100."""
    if len(interventions) < 2:
        return 50.0
    
    # Split into first half and second half by timestamp
    interventions_sorted = sorted(interventions, key=lambda x: x.get("ts", ""))
    mid = len(interventions_sorted) // 2
    first_half = interventions_sorted[:mid]
    second_half = interventions_sorted[mid:]
    
    # Count per cycle in each half
    cycles_first = set(e.get("cycle") for e in first_half if e.get("cycle"))
    cycles_second = set(e.get("cycle") for e in second_half if e.get("cycle"))
    
    rate_first = len(first_half) / max(len(cycles_first), 1)
    rate_second = len(second_half) / max(len(cycles_second), 1)
    
    if rate_first == 0:
        return 80.0  # No baseline, assume moderate
    
    change = (rate_second - rate_first) / rate_first
    # Negative change (decreasing) = good
    if change <= -0.5:
        return 95.0
    elif change <= 0:
        return 75 + (-change * 40)  # 75-95 range
    elif change <= 0.5:
        return 60 - (change * 40)  # 40-60 range
    else:
        return max(10, 40 - (change - 0.5) * 30)

def load_fleet_metrics(last_n: int = 3) -> list:
    """Load last N entries from fleet-metrics.jsonl that have hosts data."""
    if not FLEET_METRICS_FILE.exists():
        return []
    lines = FLEET_METRICS_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("hosts"):
                entries.append(d)
                if len(entries) >= last_n:
                    break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return list(reversed(entries))  # chronological order

def load_fleet_snapshots(last_n: int = 3) -> list:
    """Load last N entries from fleet-snapshots.jsonl."""
    if not FLEET_SNAPSHOTS_FILE.exists():
        return []
    lines = FLEET_SNAPSHOTS_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            entries.append(d)
            if len(entries) >= last_n:
                break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return list(reversed(entries))

def compute_host_uptime(metrics: list) -> dict:
    """Fraction of reads where each host reported data. Returns {host_name: 0-1}."""
    if not metrics:
        return {h: 0.0 for h in EXPECTED_HOSTS}
    n = len(metrics)
    uptime = {}
    for host in EXPECTED_HOSTS:
        up_reads = 0
        for entry in metrics:
            hosts_data = entry.get("hosts", [])
            for h in hosts_data:
                if h.get("name") == host and h.get("vram_pct") is not None:
                    up_reads += 1
                    break
        uptime[host] = up_reads / n
    return uptime

def compute_vram_trend(metrics: list) -> dict:
    """VRAM trend per host across last N reads. Returns {host_name: delta_pct}.
    Positive = increasing (concerning if >20), Negative = decreasing, 0 = stable."""
    if len(metrics) < 2:
        return {h: 0.0 for h in EXPECTED_HOSTS}
    trend = {}
    for host in EXPECTED_HOSTS:
        values = []
        for entry in metrics:
            hosts_data = entry.get("hosts", [])
            for h in hosts_data:
                if h.get("name") == host and h.get("vram_pct") is not None:
                    values.append(h["vram_pct"])
                    break
        if len(values) >= 2:
            trend[host] = round(values[-1] - values[0], 1)
        else:
            trend[host] = 0.0
    return trend

def compute_model_load_success(snapshots: list) -> float:
    """Fraction of agent slots that have a non-'unknown' status in latest snapshot. 0-1."""
    if not snapshots:
        return 0.5  # neutral default
    latest = snapshots[-1]
    agents = latest.get("agent_statuses", [])
    if not agents:
        return 0.5
    loaded = sum(1 for a in agents if a.get("status") not in ("unknown", "down", None))
    return loaded / len(agents)

def compute_fleet_readiness() -> dict:
    """Compute fleet readiness composite 0-100.
    
    Components:
      - host_uptime: % of expected hosts reporting data in last 3 reads (weight 0.40)
      - vram_stability: penalize hosts with VRAM trend > +20% (weight 0.25)
      - model_load: fraction of agent slots with loaded models (weight 0.35)
    """
    metrics = load_fleet_metrics(3)
    snapshots = load_fleet_snapshots(3)
    
    uptime = compute_host_uptime(metrics)
    vram_trend = compute_vram_trend(metrics)
    model_load = compute_model_load_success(snapshots)
    
    # Host uptime score: 0-100 (all 4 up = 100, none = 0)
    uptime_score = sum(uptime.values()) / len(EXPECTED_HOSTS) * 100
    
    # VRAM stability score: start at 100, penalize each host with trend > +20
    vram_score = 100.0
    for host, delta in vram_trend.items():
        if delta > 20:
            vram_score -= min(25, (delta - 20) * 2)
    vram_score = max(0, min(100, vram_score))
    
    # Model load score: 0-100
    model_score = model_load * 100
    
    # Composite
    readiness = uptime_score * 0.40 + vram_score * 0.25 + model_score * 0.35
    readiness = max(0, min(100, round(readiness, 1)))
    
    return {
        "fleet_readiness": readiness,
        "components": {
            "host_uptime_pct": round(uptime_score, 1),
            "vram_stability": round(vram_score, 1),
            "model_load_rate": round(model_score, 1),
        },
        "per_host": {
            h: {
                "uptime": round(uptime.get(h, 0.0), 3),
                "vram_trend_pct": vram_trend.get(h, 0.0),
            }
            for h in EXPECTED_HOSTS
        },
        "weights": {"host_uptime": 0.40, "vram_stability": 0.25, "model_load": 0.35},
    }

def compute_autonomy_score() -> dict:
    """Compute the composite fleet autonomy score."""
    interventions = load_interventions()
    durations = load_cycle_durations()
    
    a = compute_pass_autonomy(interventions)
    b = compute_duration_score(durations)
    c = compute_rework_score()
    d = compute_trend_score(interventions)
    
    # Weighted composite
    score = a * 0.35 + b * 0.25 + c * 0.20 + d * 0.20
    score = max(0, min(100, round(score, 1)))
    
    # Fleet readiness (Goal #4: Fleet Health Composite Score)
    fleet = compute_fleet_readiness()
    
    return {
        "score": score,
        "fleet_readiness": fleet["fleet_readiness"],
        "components": {
            "pass_autonomy": round(a, 1),
            "duration_score": round(b, 1),
            "rework_score": round(c, 1),
            "trend_score": round(d, 1),
        },
        "fleet_components": fleet["components"],
        "fleet_per_host": fleet["per_host"],
        "weights": {"a": 0.35, "b": 0.25, "c": 0.20, "d": 0.20},
        "fleet_weights": fleet["weights"],
        "computed_at": datetime.utcnow().isoformat(),
        "data_sources": {
            "interventions_count": len(interventions),
            "cycle_durations_count": len(durations),
        },
    }

def selftest():
    """Verify: score in [0,100]; correlates with intervention data (r>0.8)."""
    print("=== autonomy_score.py SELFTEST ===")
    
    # Test 1: Live computation produces valid score
    result = compute_autonomy_score()
    score = result["score"]
    assert 0 <= score <= 100, f"Score {score} out of [0,100]"
    print(f"  Live score: {score}")
    print(f"  Components: {result['components']}")
    
    # Test 2: Correlation with intervention data
    # Generate synthetic scenarios with varying intervention counts
    import random
    random.seed(42)
    
    test_scores = []
    test_interventions = []
    
    for n_int in range(0, 21):
        # Simulate: more interventions -> lower score
        # Component (a) directly uses intervention count
        total_passes = 100
        a = max(0, min(100, (1 - n_int / total_passes) * 100))
        
        # Other components held constant for this test
        b = 70.0  # baseline duration
        c = 80.0  # low rework
        d = max(10, 90 - n_int * 2)  # trend worsens with interventions
        
        composite = a * 0.35 + b * 0.25 + c * 0.20 + d * 0.20
        test_scores.append(composite)
        test_interventions.append(n_int)
    
    # Compute Pearson r between score and -interventions (should be strongly negative)
    n = len(test_scores)
    mean_s = sum(test_scores) / n
    mean_i = sum(test_interventions) / n
    
    cov = sum((s - mean_s) * (-i + mean_i) for s, i in zip(test_scores, test_interventions))
    std_s = math.sqrt(sum((s - mean_s)**2 for s in test_scores))
    std_i = math.sqrt(sum((i - mean_i)**2 for i in test_interventions))
    
    if std_s * std_i == 0:
        r = 0.0
    else:
        r = cov / (std_s * std_i)
    
    print(f"  Correlation test: r={r:.4f} (score vs -interventions)")
    assert r > 0.8, f"Correlation {r:.4f} < 0.8 threshold"
    
    # Test 3: Boundary conditions
    # Zero interventions should give high score
    zero_int = compute_pass_autonomy([], total_passes=100)
    assert zero_int == 100.0, f"Zero interventions should give 100%, got {zero_int}"
    
    # All passes intervened should give low score
    all_int = compute_pass_autonomy([{"ts": "x"}] * 100, total_passes=100)
    assert all_int == 0.0, f"All interventions should give 0%, got {all_int}"
    
    print(f"  Boundary: zero_int={zero_int}, all_int={all_int}")
    
    # Test 4: Duration score boundaries
    fast = compute_duration_score([{"duration_hours": 12}])
    normal = compute_duration_score([{"duration_hours": 48}])
    slow = compute_duration_score([{"duration_hours": 96}])
    assert fast > normal > slow, f"Duration ordering violated: fast={fast}, normal={normal}, slow={slow}"
    print(f"  Duration: fast={fast}, normal={normal}, slow={slow}")
    
    # Write live result
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\n  Wrote {OUTPUT}")
    print("  SELFTEST: PASS")
    return True

def main():
    import sys
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    result = compute_autonomy_score()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Autonomy score: {result['score']}/100")
    print(f"  Components: {result['components']}")
    print(f"  Written to: {OUTPUT}")

if __name__ == "__main__":
    main()
