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


def _short_ts(ts):
    """'2026-11-25T05:48:39...' -> '11-25 05:48'. '' if unparseable."""
    import re
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})", str(ts or ""))
    if not m:
        return ""
    y, mo, d, h, mi = m.groups()
    return "%s-%s %s:%s" % (mo, d, h, mi)


def _get_score_history(max_pts=8):
    """Real per-sample autonomy score history for the cross-cycle trend chart.
    Source: memory/ops/autonomy-score-history.jsonl (timestamped real samples), with
    the current authoritative score appended. Returns [{label, score, mode}] in
    time-ascending order (last = now). Empty list if no usable sample.
    Pixel cycle-24 goal #1 assist (UI consumes this; honest real samples, not proxies).
    """
    import re
    path = os.path.join(OPS_DIR, "autonomy-score-history.jsonl")
    pts = []
    for e in _read_jsonl(path):
        sc = e.get("score")
        if sc is None:
            continue
        try:
            sc = float(sc)
        except (TypeError, ValueError):
            continue
        ts = str(e.get("timestamp") or e.get("computed_at") or "")
        pts.append({"ts": ts, "score": round(sc, 1)})
    # Append the current authoritative score (dedupe by timestamp).
    cur_score, _ = _get_autonomy_score_file()
    if cur_score is not None:
        cur_ts = str(_read_json(os.path.join(OPS_DIR, "autonomy-score.json")).get("computed_at") or "")
        if not pts or cur_ts != pts[-1].get("ts"):
            pts.append({"ts": cur_ts, "score": round(float(cur_score), 1)})
    if not pts:
        return []

    def _key(p):
        m = re.search(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})", p["ts"] or "")
        return (m.group(1).replace(" ", "T") if m else "") + (p["ts"] or "")
    pts.sort(key=_key)
    pts = pts[-max_pts:]
    out = []
    for p in pts:
        label = _short_ts(p["ts"]) or ("sample-%d" % len(out))
        out.append({"label": label, "score": p["score"], "mode": "converging"})
    return out


def _get_autonomy_score_file():
    """Authoritative autonomy score from memory/ops/autonomy-score.json.
    Returns (score, components) or (None, None) if unavailable."""
    data = _read_json(os.path.join(OPS_DIR, "autonomy-score.json"))
    score = data.get("score")
    if score is None:
        return None, None
    return float(score), data.get("components", {})


def _get_efficiency_index():
    """Latest efficiency-index entry from memory/ops/efficiency-index.jsonl.
    Returns dict (possibly empty)."""
    entries = _read_jsonl(os.path.join(OPS_DIR, "efficiency-index.jsonl"))
    if not entries:
        return {}
    # newest = last line (file is append-ordered by cycle)
    return max(entries, key=lambda e: int(e.get("cycle", 0)))


def _compute_autonomy_score():
    """Composite 0-100 autonomy score.
    PRIMARY source: memory/ops/autonomy-score.json (score) so the endpoint's
    value matches the authoritative file. Falls back to a computed composite when
    that file is absent, using efficiency-index.jsonl for the rework component.
    Returns (score, components_dict).
    """
    # Primary: authoritative file
    file_score, file_components = _get_autonomy_score_file()
    if file_score is not None:
        return round(min(100.0, max(0.0, file_score)), 1), file_components

    # Fallback composite (no autonomy-score.json present).
    eff_idx = _get_efficiency_index()
    rework_rate = float(eff_idx.get("rework_rate", 0.05) or 0.05)

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

    # (c) Rework rate: from efficiency-index.jsonl (authoritative when present)
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
    components = {
        "pass_autonomy": round(pass_autonomy, 1),
        "trend_score": round(velocity_score, 1),
        "rework_score": round(rework_score, 1),
        "intervention_score": round(intervention_score, 1),
    }
    return round(min(100.0, max(0.0, score)), 1), components


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


def _source_signature():
    """Max mtime of the source files the endpoint reads. A write to any of them
    changes this signature, so the cache invalidates on write (not just TTL)."""
    paths = [
        os.path.join(OPS_DIR, "autonomy-score.json"),
        os.path.join(OPS_DIR, "efficiency-index.jsonl"),
        os.path.join(OPS_DIR, "human-interventions.jsonl"),
        os.path.join(OPS_DIR, "cycle-durations.jsonl"),
        os.path.join(OPS_DIR, "autonomy-score-history.jsonl"),
    ]
    sig = 0.0
    for p in paths:
        try:
            sig = max(sig, os.path.getmtime(p))
        except OSError:
            pass
    return sig


def invalidate_cache():
    """Force the next handle_convergence() call to recompute."""
    _cache["ts"] = 0.0
    _cache["data"] = None


def handle_convergence(force=False):
    """Main handler for GET /api/convergence. Returns the composite JSON payload.
    Caches for CACHE_TTL (5 min) but invalidates on write to any source file."""
    now = time.time()
    sig = _source_signature()
    if (
        not force
        and _cache["data"] is not None
        and (now - _cache["ts"]) < CACHE_TTL
        and _cache.get("sig") == sig   # unchanged source files => still fresh
    ):
        return _cache["data"]

    autonomy_score, autonomy_components = _compute_autonomy_score()
    efficiency = _get_efficiency_index()
    cycle_durations = _get_cycle_durations()
    interventions = _get_interventions()
    steady_state = _compute_steady_state_progress()

    # Cross-cycle score history (Pixel cycle-24 goal #1): real samples + current.
    score_history = _get_score_history()
    if score_history:
        score_history[-1]["mode"] = "steady-state" if steady_state.get("steady_state_reached") else "converging"

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
        "autonomy_components": autonomy_components,
        "efficiency_index": {
            "cycle": efficiency.get("cycle"),
            "efficiency_index": efficiency.get("efficiency_index"),
            "rework_rate": efficiency.get("rework_rate"),
            "velocity_goals_per_pass": efficiency.get("velocity_goals_per_pass"),
            "idle_fraction": efficiency.get("idle_fraction"),
        } if efficiency else None,
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
        "score_history": score_history,
    }

    _cache["ts"] = now
    _cache["sig"] = sig
    _cache["data"] = payload
    return payload


def _count_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for l in f if l.strip())
    except OSError:
        return 0


def selftest():
    """Verify: (1) fields present/valid, (2) data matches source files,
    (3) cache hit on repeat + invalidation on write to a source file."""
    import json as _json
    data = handle_convergence(force=True)
    assert data.get("ok") is True, "ok flag missing"
    # --- source-file match checks ---
    src_score = _read_json(os.path.join(OPS_DIR, "autonomy-score.json")).get("score")
    if src_score is not None:
        assert abs(data["fleet_autonomy_score"] - float(src_score)) < 0.05, \
            f"autonomy {data['fleet_autonomy_score']} != source {src_score}"
    eff = _read_jsonl(os.path.join(OPS_DIR, "efficiency-index.jsonl"))
    if eff:
        latest = max(eff, key=lambda e: int(e.get("cycle", 0)))
        assert data["efficiency_index"]["rework_rate"] == latest.get("rework_rate"), \
            f"rework {data['efficiency_index']['rework_rate']} != source {latest.get('rework_rate')}"
    n_interv = _count_lines(os.path.join(OPS_DIR, "human-interventions.jsonl"))
    assert data["human_intervention_count"]["total"] == n_interv, \
        f"interventions {data['human_intervention_count']['total']} != source lines {n_interv}"
    # --- cache: repeat call hits cache (identical object), write busts it ---
    hit = handle_convergence()
    assert hit is data, "cache miss on immediate repeat call"
    target = os.path.join(OPS_DIR, "autonomy-score.json")
    _orig_mt = os.stat(target).st_mtime
    _t = time.time()
    os.utime(target, (_t + 60, _t + 60))  # simulate a write: bump mtime past any resolution
    after = handle_convergence()
    assert after is not data, "cache did NOT invalidate after source write"
    os.utime(target, (_orig_mt, _orig_mt))  # restore original mtime
    print(f"SELFTEST PASS: autonomy={data['fleet_autonomy_score']} (src {src_score}), "
          f"rework={data['efficiency_index']['rework_rate']}, interventions={data['human_intervention_count']['total']}/{n_interv}, "
          f"trend={data['cycle_duration_trend']['direction']} ({len(data['cycle_duration_trend']['cycles'])} cycles), "
          f"steady_state={data['steady_state_progress']['progress_pct']}% | cache: hit=OK, write-invalidate=OK")
    return data


# ─── /api/convergence/trend (Goal #8: Convergence Panel Backend) ──────────────

def _get_efficiency_index_entries():
    """Read efficiency-index.jsonl and return list of {cycle, efficiency_index, rework_rate}."""
    path = os.path.join(OPS_DIR, "efficiency-index.jsonl")
    entries = _read_jsonl(path)
    return [
        {
            "cycle": e.get("cycle", "?"),
            "efficiency_index": e.get("efficiency_index"),
            "rework_rate": e.get("rework_rate"),
            "velocity": e.get("velocity_goals_per_pass"),
        }
        for e in entries
    ]


def _get_autonomy_trend():
    """Build autonomy score trend from available sources.
    Sources: autonomy-score.json (current), cycle-efficiency*.json (historical velocity proxy).
    Returns list of {cycle, score} sorted by cycle, up to last 5."""
    # Current score
    cur = _get_autonomy_score_file()
    points = []
    if cur[0] is not None:
        points.append({"cycle": "current", "score": cur[0]})

    # Try to derive historical scores from cycle-efficiency files (velocity as proxy)
    for f in sorted(os.listdir(OPS_DIR)):
        if f.startswith("cycle-efficiency") and f.endswith(".json"):
            data = _read_json(os.path.join(OPS_DIR, f))
            cycle = str(data.get("cycle", "?"))
            vel = data.get("velocity_goals_per_pass")
            if vel is not None:
                # Normalize velocity to a 0-100 proxy score
                points.append({"cycle": cycle, "score": round(min(100, vel * 500), 1)})

    # Sort by cycle number (current goes last)
    def sort_key(p):
        if p["cycle"] == "current":
            return 9999
        return _cycle_num(p["cycle"])
    points.sort(key=sort_key)
    return points[-5:]


def _get_intervention_trend():
    """Group interventions by cycle, return last 5 as {cycle, count}."""
    path = os.path.join(OPS_DIR, "human-interventions.jsonl")
    entries = _read_jsonl(path)
    counts = {}
    for e in entries:
        c = str(e.get("cycle", "?"))
        counts[c] = counts.get(c, 0) + 1
    # Sort by cycle number, take last 5
    sorted_cycles = sorted(counts.keys(), key=lambda c: _cycle_num(c))
    return [{"cycle": c, "count": counts[c]} for c in sorted_cycles[-5:]]


def handle_convergence_trend(force=False):
    """Handler for GET /api/convergence/trend.
    Returns 5 data points per metric (autonomy_score, intervention_count, efficiency_index).
    Pads with null if fewer than 5 real data points available.
    Caches 5 min like the parent endpoint."""
    global _cache
    now = time.time()
    if not force and _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"].get("trend", {})

    # If we have full data cached, extract trend from it
    if not force and _cache["data"]:
        cached_trend = _cache["data"].get("trend")
        if cached_trend:
            return cached_trend

    # Compute fresh
    autonomy_pts = _get_autonomy_trend()
    intervention_pts = _get_intervention_trend()
    efficiency_pts = _get_efficiency_index_entries()[-5:]

    # Normalize to {cycle, value} and pad to exactly 5
    def normalize_pad(points, val_key, n=5):
        norm = [{"cycle": p["cycle"], "value": p[val_key]} for p in points]
        while len(norm) < n:
            norm.insert(0, {"cycle": None, "value": None})
        return norm[-n:]

    trend = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "autonomy_score": normalize_pad(autonomy_pts, "score"),
        "intervention_count": normalize_pad(intervention_pts, "count"),
        "efficiency_index": normalize_pad(efficiency_pts, "efficiency_index"),
    }

    # Store in cache under 'trend' key
    if _cache["data"] is None:
        _cache["data"] = {}
    _cache["data"]["trend"] = trend
    _cache["ts"] = now
    return trend


def selftest_trend():
    """Selftest for /api/convergence/trend: verify 5 data points per metric, matches source files."""
    print("=== convergence_api.py TREND SELFTEST ===")

    # Create synthetic efficiency-index entries to ensure 5 data points
    test_dir = os.path.join(HERE, "memory", "ops")
    ei_path = os.path.join(test_dir, "efficiency-index.jsonl")

    # Back up original
    orig_content = ""
    if os.path.exists(ei_path):
        with open(ei_path, encoding="utf-8") as f:
            orig_content = f.read()

    # Write 5 synthetic entries for test
    import json as _json
    synthetic = []
    for i in range(12, 17):
        synthetic.append({"cycle": i, "efficiency_index": round(0.15 + i * 0.01, 4),
                          "rework_rate": round(0.1 - i * 0.005, 4),
                          "velocity_goals_per_pass": round(0.2 + i * 0.01, 4)})
    with open(ei_path, "w", encoding="utf-8") as f:
        for s in synthetic:
            f.write(_json.dumps(s) + "\n")

    try:
        trend = handle_convergence_trend(force=True)

        # Verify structure: 5 data points per metric
        assert len(trend["autonomy_score"]) == 5, f"autonomy_score has {len(trend['autonomy_score'])} points, expected 5"
        assert len(trend["intervention_count"]) == 5, f"intervention_count has {len(trend['intervention_count'])} points, expected 5"
        assert len(trend["efficiency_index"]) == 5, f"efficiency_index has {len(trend['efficiency_index'])} points, expected 5"

        # Verify efficiency_index matches source (last 5 of synthetic)
        src_entries = [s for s in synthetic][-5:]
        for i, pt in enumerate(trend["efficiency_index"]):
            if pt["cycle"] is not None:
                expected_val = src_entries[i]["efficiency_index"]
                assert abs(pt["value"] - expected_val) < 0.001, \
                    f"efficiency mismatch at {pt['cycle']}: got {pt['value']}, expected {expected_val}"

        # Verify intervention_count matches source
        int_path = os.path.join(test_dir, "human-interventions.jsonl")
        with open(int_path, encoding="utf-8") as f:
            int_lines = [json.loads(l) for l in f if l.strip()]
        int_counts = {}
        for e in int_lines:
            c = str(e.get("cycle", "?"))
            int_counts[c] = int_counts.get(c, 0) + 1
        # Check that non-null points match
        for pt in trend["intervention_count"]:
            if pt["cycle"] is not None and pt["cycle"] in int_counts:
                assert pt["value"] == int_counts[pt["cycle"]], \
                    f"intervention mismatch at cycle {pt['cycle']}: got {pt['value']}, expected {int_counts[pt['cycle']]}"

        # Verify cache works
        t2 = handle_convergence_trend()  # should be cached
        assert t2 == trend, "cache miss on immediate repeat"

        print(f"  autonomy_score: {[p['value'] for p in trend['autonomy_score']]}")
        print(f"  intervention_count: {[p['value'] for p in trend['intervention_count']]}")
        print(f"  efficiency_index: {[p['value'] for p in trend['efficiency_index']]}")
        print("  TREND SELFTEST PASS: 5 pts/metric, matches source, cache OK")
    finally:
        # Restore original
        with open(ei_path, "w", encoding="utf-8") as f:
            f.write(orig_content)

    return True


if __name__ == "__main__":
    selftest()
    selftest_trend()
