"""Cycle Closeout Convergence API - /api/convergence/closeout handler.
Designer cycle-20 goal #9 (2026-11-26).

Returns the data shape defined in memory/ops/convergence-section-layout-spec.md:
  autonomy_score, delta_vs_prev, interventions, goal_completion, cycle_mode,
  trend_5_cycles, steady_state_criteria, regressions, watch_items.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS = os.path.join(HERE, "memory", "ops")
GOALS = os.path.join(HERE, "memory", "goals")

_cache = {"ts": 0.0, "data": None}
TTL = 300


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _read_jsonl(path, n=500):
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()[-n:]
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


def _get_autonomy_score():
    """Current + previous autonomy score from ops file."""
    data = _read_json(os.path.join(OPS, "autonomy-score.json"))
    score = data.get("score")
    prev = data.get("prev_score")
    return (float(score) if score is not None else None,
            float(prev) if prev is not None else None)


def _get_trend():
    """Last 5 autonomy scores from velocity-trend.json or efficiency files."""
    vt = _read_json(os.path.join(OPS, "velocity-trend.json"))
    cycles = vt.get("cycles", [])
    if len(cycles) >= 2:
        return [c.get("score", c.get("autonomy_score", 0)) for c in cycles[-5:]]
    # Fallback: derive from efficiency files
    scores = []
    for f in sorted(os.listdir(OPS)):
        if f.startswith("cycle-efficiency") and f.endswith(".json"):
            d = _read_json(os.path.join(OPS, f))
            s = d.get("autonomy_score") or d.get("score")
            if s is not None:
                scores.append(float(s))
    return scores[-5:] if scores else []


def _get_interventions():
    """Count + types of human interventions this cycle."""
    entries = _read_jsonl(os.path.join(OPS, "human-interventions.jsonl"))
    # Get latest cycle number
    cycles = set(str(e.get("cycle", "?")) for e in entries)
    if not cycles:
        return {"count": 0, "types": []}
    latest = max(cycles, key=lambda c: int(re.search(r'\d+', c).group()) if re.search(r'\d+', c) else 0)
    types = []
    count = 0
    for e in entries:
        if str(e.get("cycle", "?")) == latest:
            count += 1
            t = e.get("type", e.get("action", "unknown"))
            if t not in types:
                types.append(t)
    return {"count": count, "types": types}


def _get_goal_completion():
    """Aggregate goal reached/total from goal_ledger or per-lane files."""
    ledger = _read_json(os.path.join(HERE, "goal_ledger.json"))
    if ledger and isinstance(ledger, dict):
        lanes = ledger.get("lanes", {})
        reached = 0
        total = 0
        for lane, data in lanes.items():
            g = data.get("goals", [])
            for goal in g:
                total += 1
                if goal.get("status") in ("verified", "reached", "closed"):
                    reached += 1
        if total > 0:
            return {"reached": reached, "total": total, "pct": round(reached / total * 100, 2)}
    # Fallback: count from per-lane goal files
    reached = 0
    total = 0
    for f in os.listdir(GOALS):
        if not f.endswith(".md") or f.startswith(("closed", "archive", "next10", "forecast", "calibration", "cycle-proposal")):
            continue
        try:
            content = open(os.path.join(GOALS, f), encoding="utf-8").read()
            # Count numbered goals and verified markers
            nums = re.findall(r'^\d+\.\s', content, re.MULTILINE)
            verified = len(re.findall(r'\(verified:', content))
            total += len(nums)
            reached += min(verified, len(nums))
        except OSError:
            pass
    if total > 0:
        return {"reached": reached, "total": total, "pct": round(reached / total * 100, 2)}
    return {"reached": 0, "total": 0, "pct": 0}


def _get_cycle_mode():
    data = _read_json(os.path.join(OPS, "fleet-mode.json"))
    return data.get("mode", "WORK")


def _get_steady_state_criteria():
    """Evaluate the 3 steady-state entry criteria."""
    score, _ = _get_autonomy_score()
    iv = _get_interventions()
    gc = _get_goal_completion()

    # Criterion 1: All lanes 10/10 sustained (1 full cycle)
    all_10 = gc["total"] > 0 and gc["reached"] == gc["total"]

    # Criterion 2: Zero human interventions for N consecutive cycles (N=3)
    entries = _read_jsonl(os.path.join(OPS, "human-interventions.jsonl"))
    zero_iv = len(entries) == 0 or iv["count"] == 0

    # Criterion 3: Autonomy score >= 90 for 3 consecutive measurements
    trend = _get_trend()
    score_gt90 = len(trend) >= 3 and all(s >= 90 for s in trend[-3:])

    return [
        {"label": "All lanes 10/10 sustained (1 cycle)", "met": bool(all_10)},
        {"label": "Zero human interventions for 3 consecutive cycles", "met": bool(zero_iv)},
        {"label": "Autonomy score >= 90 for 3 consecutive measurements", "met": bool(score_gt90)}
    ]


def _get_regressions_and_watches():
    """Derive regressions (score drops) and watch items (low-completion lanes)."""
    regressions = []
    watches = []
    score, prev = _get_autonomy_score()
    if score is not None and prev is not None and prev - score > 3:
        regressions.append(f"Autonomy score dropped {prev:.1f} → {score:.1f}")
    gc = _get_goal_completion()
    if gc["total"] > 0 and gc["pct"] < 80:
        watches.append(f"Goal completion at {gc['pct']:.0f}% — below 80% target")
    return regressions, watches


def handle_closeout():
    """Build the closeout data shape per convergence-section-layout-spec.md."""
    import time
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    score, prev = _get_autonomy_score()
    delta = round(score - prev, 1) if (score is not None and prev is not None) else None
    regrs, watches = _get_regressions_and_watches()

    data = {
        "autonomy_score": score,
        "delta_vs_prev": delta,
        "interventions": _get_interventions(),
        "goal_completion": _get_goal_completion(),
        "cycle_mode": _get_cycle_mode(),
        "trend_5_cycles": _get_trend(),
        "steady_state_criteria": _get_steady_state_criteria(),
        "regressions": regrs,
        "watch_items": watches
    }
    _cache["ts"] = now
    _cache["data"] = data
    return data
