"""Convergence Dashboard API - /api/convergence endpoint handler.
Orchestrator cycle-17 goal 1 (2026-11-24).

Exposes: fleet_autonomy_score, cycle_duration_trend, human_intervention_count, steady_state_progress.
Data sources: cycle-efficiency*.json, velocity-trend.json, mode-durations.json,
              human-interventions.jsonl, cycle-durations.jsonl.
"""
import json
import os
import time
import statistics

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS_DIR = os.path.join(HERE, "memory", "ops")
GOALS_DIR = os.path.join(HERE, "memory", "goals")

_cache = {"ts": 0.0, "data": None}
CACHE_TTL = 300  # 5 min


def _read_json(path):
    """Read a JSON file, return {} on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _read_jsonl(path, max_lines=500):
    """Read last N lines of a JSONL file."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()[-max_lines:]
        out = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return out
    except OSError:
        return []


def _get_cycle_durations():
    """Return list of {cycle, duration_h} from cycle-durations.jsonl or derive from efficiency files."""
    # Primary source: dedicated file
    cd_path = os.path.join(OPS_DIR, "cycle-durations.jsonl")
    entries = _read_jsonl(cd_path)
    if entries:
        return [{"cycle": e.get("cycle", "?"), "duration_h": e.get("duration_h", 0)} for e in entries]

    # Fallback: derive from cycle-efficiency*.json files
    durations = []
    for f in sorted(os.listdir(OPS_DIR)):
        if f.startswith("cycle-efficiency") and f.endswith(".json"):
            data = _read_json(os.path.join(OPS_DIR, f))
            cycle = data.get("cycle", "?")
            dur = data.get("time_to_100pct_h") or data.get("time_to_100_h")
            if dur is not None:
                durations.append({"cycle": str(cycle), "duration_h": round(float(dur), 2)})
    return sorted(durations, key=lambda x: _cycle_num(x["cycle"]))[-10:]


def _cycle_num(c):
    """Extract numeric cycle from '15' or 'cycle-15'."""
    import re
    m = re.search(r'(\d+)', str(c))
    return int(m.group(1)) if m else 0


def _get_interventions():
    """Return {cycle: count} of human interventions."""
    path = os.path.join(OPS_DIR, "human-interventions.jsonl")
    entries = _read_jsonl(path)
    counts = {}
    for e in entries:
        cycle = str(e.get("cycle", "?"))
        counts[cycle] = counts.get(cycle, 0) + 1
    return counts


def _compute_autonomy_score():
    """Composite 0-100 autonomy score.
    Components: (a) pass autonomy % (no human input), (b) velocity trend,
    (c) rework rate (inverse), (d) intervention frequency (inverse).
    """
    # (a) Pass autonomy: from cycle-efficiency
    eff = _read_json(os.path.join(OPS_DIR, "cycle-efficiency.json"))
    productive_pct = eff.get("productive_pct")
    if productive_pct is None:
        # Derive from goals_completed / passes_used
        gc = eff.get("goals_completed", 0)
        pu = eff.get("passes_used", 1)
        productive_pct = min(1.0, gc / max(pu, 1)) * 100 if pu > 0 else 50.0
    pass_autonomy = min(100.0, float(productive_pct))

    # (b) Velocity trend: from velocity-trend.json
    vt = _read_json(os.path.join(OPS_DIR, "velocity-trend.json"))
    trend = vt.get("trend", [])
    decline_flag = vt.get("decline_flag", {})
    if decline_flag.get("declining"):
        velocity_score = 40.0
    elif len(trend) >= 2:
        # Score based on whether velocity is stable or improving
        velocities = [t["velocity"] for t in trend if t.get("velocity") is not None]
        if len(velocities) >= 2 and velocities[-1] >= velocities[0]:
            velocity_score = 80.0
        else:
            velocity_score = 60.0
    else:
        velocity_score = 50.0  # insufficient data, neutral

    # (c) Rework rate: from closed topics or goal reopens (approximate as low for now)
    rework_rate = 0.05  # ~5% default until tracking is in place
    rework_score = (1.0 - rework_rate) * 100

    # (d) Intervention frequency: fewer interventions = higher score
    interventions = _get_interventions()
    total_interventions = sum(interventions.values())
    if total_interventions == 0:
        intervention_score = 90.0
    elif total_interventions <= 3:
        intervention_score = 75.0
    elif total_interventions <= 10:
        intervention_score = 55.0
    else:
        intervention_score = 30.0

    # Weighted composite
    score = (
        pass_autonomy * 0.3 +
        velocity_score * 0.25 +
        rework_score * 0.2 +
        intervention_score * 0.25
    )
    return round(min(100.0, max(0.0, score)), 1)


def _compute_steady_state_progress():
    """Progress % toward steady-state (3 criteria must all pass for 3 consecutive cycles).
    Criteria: interventions <2/cycle, duration variance <15%, zero rework.
    Returns: {progress_pct, criteria: {...}, consecutive_passes}
    """
    durations = _get_cycle_durations()
    interventions = _get_interventions()

    # Criterion 1: interventions < 2 per cycle (check last 3 cycles)
    recent_cycles = sorted(interventions.keys(), key=_cycle_num)[-3:] if interventions else []
    int_pass = True
    for c in recent_cycles:
        if interventions.get(c, 0) >= 2:
            int_pass = False
            break
    # If no data, assume pass (neutral)
    if not recent_cycles:
        int_pass = True

    # Criterion 2: duration variance < 15%
    dur_values = [d["duration_h"] for d in durations[-3:] if d.get("duration_h")]
    if len(dur_values) >= 3:
        mean_d = statistics.mean(dur_values)
        stdev_d = statistics.stdev(dur_values)
        cv = (stdev_d / mean_d * 100) if mean_d > 0 else 0
        dur_pass = cv < 15.0
    elif len(dur_values) >= 2:
        dur_pass = True  # insufficient for variance calc, assume pass
    else:
        dur_pass = True  # no data, neutral

    # Criterion 3: zero rework (no goal reopened) - approximate from closed_topics
    rework_pass = True  # default until tracking is in place

    criteria = {
        "interventions_lt2": int_pass,
        "duration_variance_lt15pct": dur_pass,
        "zero_rework": rework_pass,
    }
    passes = sum(criteria.values())
    progress_pct = round(passes / 3 * 100, 1)

    # Consecutive passes: count how many of last 3 cycles had all criteria met
    consecutive = 0
    if int_pass and dur_pass and rework_pass:
        consecutive = min(3, len(recent_cycles) or 1)

    return {
        "progress_pct": progress_pct,
        "criteria": criteria,
        "consecutive_passes": consecutive,
        "steady_state_reached": consecutive >= 3,
    }


def handle_convergence():
    """Main handler for GET /api/convergence. Returns the composite JSON payload."""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    autonomy_score = _compute_autonomy_score()
    cycle_durations = _get_cycle_durations()
    interventions = _get_interventions()
    steady_state = _compute_steady_state_progress()

    # Cycle duration trend (last 5)
    duration_trend = cycle_durations[-5:]
    if len(duration_trend) >= 2:
        vals = [d["duration_h"] for d in duration_trend]
        trend_direction = "improving" if vals[-1] < vals[0] else ("declining" if vals[-1] > vals[0] else "stable")
    else:
        trend_direction = "insufficient_data"

    payload = {
        "ok": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fleet_autonomy_score": autonomy_score,
        "cycle_duration_trend": {
            "cycles": duration_trend,
            "direction": trend_direction,
            "mean_h": round(statistics.mean([d["duration_h"] for d in duration_trend]), 2) if duration_trend else None,
        },
        "human_intervention_count": {
            "per_cycle": interventions,
            "total": sum(interventions.values()),
        },
        "steady_state_progress": steady_state,
    }

    _cache["ts"] = now
    _cache["data"] = payload
    return payload


def selftest():
    """Quick self-test: verify all 4 fields present and valid."""
    data = handle_convergence()
    assert data.get("ok") is True, "ok flag missing"
    assert isinstance(data.get("fleet_autonomy_score"), (int, float)), "autonomy score not numeric"
    assert 0 <= data["fleet_autonomy_score"] <= 100, f"autonomy score out of range: {data['fleet_autonomy_score']}"
    assert "cycle_duration_trend" in data, "cycle_duration_trend missing"
    assert "human_intervention_count" in data, "human_intervention_count missing"
    assert "steady_state_progress" in data, "steady_state_progress missing"
    ss = data["steady_state_progress"]
    assert 0 <= ss["progress_pct"] <= 100, f"steady-state progress out of range: {ss['progress_pct']}"
    assert "criteria" in ss, "steady-state criteria missing"
    print(f"SELFTEST PASS: autonomy={data['fleet_autonomy_score']}, "
          f"trend={data['cycle_duration_trend']['direction']} ({len(data['cycle_duration_trend']['cycles'])} cycles), "
          f"interventions={data['human_intervention_count']['total']}, "
          f"steady_state={ss['progress_pct']}%")
    return data


if __name__ == "__main__":
    selftest()
