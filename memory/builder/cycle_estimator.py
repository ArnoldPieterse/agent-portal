#!/usr/bin/env python3
"""
Cycle Estimator: predicts when the fleet will reach steady-state convergence.

Reads:
  - memory/ops/efficiency-index.jsonl (per-cycle metrics)
  - memory/ops/autonomy-score.json (current autonomy score + components)
  - memory/fleet/fleet-mode.json (current mode)

Writes:
  - memory/fleet/fleet-mode.json: adds 'cycle_estimate' field

Usage:
  python memory/builder/cycle_estimator.py          # compute + write
  python memory/builder/cycle_estimator.py --dry    # compute only, print JSON
"""
import json
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EFFICIENCY_PATH = os.path.join(BASE, 'memory', 'ops', 'efficiency-index.jsonl')
AUTONOMY_PATH = os.path.join(BASE, 'memory', 'ops', 'autonomy-score.json')
FLEET_MODE_PATH = os.path.join(BASE, 'memory', 'fleet', 'fleet-mode.json')

# Steady-state target: autonomy_score >= 90, rework_rate < 0.05, interventions/cycle < 1
TARGET_AUTONOMY = 90.0
TARGET_REWORK = 0.05
TARGET_INTERVENTIONS_PER_CYCLE = 1.0


def _read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _read_jsonl(path):
    records = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception:
        pass
    return records


def estimate():
    """Compute cycle convergence estimate. Returns dict with fields:
    - cycles_remaining: int (estimated)
    - eta_date: ISO date string
    - confidence: float 0-1
    - trend: 'accelerating' | 'steady' | 'decelerating'
    - basis: str (human-readable summary)
    """
    efficiency = _read_jsonl(EFFICIENCY_PATH)
    autonomy_data = _read_json(AUTONOMY_PATH) or {}
    fleet_mode = _read_json(FLEET_MODE_PATH) or {}

    current_autonomy = autonomy_data.get('score', 0.0)
    # Normalize to 0-100 scale if needed (some files store 0-1)
    if current_autonomy <= 1.0:
        current_autonomy *= 100

    cycles_done = len(efficiency)

    if cycles_done == 0:
        return {
            'cycles_remaining': -1,
            'eta_date': None,
            'confidence': 0.0,
            'trend': 'unknown',
            'basis': 'No cycle history available'
        }

    # Compute average per-cycle improvement in autonomy score
    # We use efficiency index as a proxy when we don't have per-cycle autonomy scores
    indices = [r.get('index', 0) for r in efficiency]
    if len(indices) >= 2:
        avg_gain_per_cycle = (indices[-1] - indices[0]) / max(len(indices) - 1, 1)
    else:
        avg_gain_per_cycle = 0.0

    # Gap to target (on 0-1 scale for efficiency; 0-100 for autonomy)
    gap_autonomy = max(TARGET_AUTONOMY - current_autonomy, 0) / 100.0  # normalize to 0-1
    gap_efficiency = max(1.0 - indices[-1], 0) if indices else 1.0

    # Use the larger gap (conservative)
    effective_gap = max(gap_autonomy, gap_efficiency * 0.5)

    if avg_gain_per_cycle > 0:
        cycles_remaining = int(effective_gap / avg_gain_per_cycle) + 1
    else:
        # No clear trend; assume 3 more cycles (pessimistic but bounded)
        cycles_remaining = 3

    # Confidence: higher with more data points and consistent trend
    if len(indices) >= 4:
        confidence = min(0.9, 0.5 + 0.1 * len(indices))
    elif len(indices) >= 2:
        confidence = 0.4 + 0.1 * len(indices)
    else:
        confidence = 0.3

    # Trend classification
    if len(indices) >= 3:
        recent_gain = (indices[-1] - indices[-2])
        prior_gain = (indices[-2] - indices[-3])
        if recent_gain > prior_gain * 1.2:
            trend = 'accelerating'
        elif recent_gain < prior_gain * 0.8:
            trend = 'decelerating'
        else:
            trend = 'steady'
    else:
        trend = 'steady' if avg_gain_per_cycle >= 0 else 'decelerating'

    # ETA: assume ~1 cycle per day (current cadence)
    from datetime import timedelta
    eta_dt = datetime.now(timezone.utc) + timedelta(days=cycles_remaining)
    eta_date = eta_dt.strftime('%Y-%m-%d')

    basis = (
        f"{cycles_done} cycles done, autonomy={current_autonomy:.0f}/100, "
        f"avg_gain/cycle={avg_gain_per_cycle:.3f}, gap={effective_gap:.3f}"
    )

    return {
        'cycles_remaining': cycles_remaining,
        'eta_date': eta_date,
        'confidence': round(confidence, 2),
        'trend': trend,
        'basis': basis
    }


def write_to_fleet_mode(estimate_data):
    """Merge cycle_estimate into fleet-mode.json (preserving existing fields)."""
    fleet_mode = _read_json(FLEET_MODE_PATH) or {}
    fleet_mode['cycle_estimate'] = estimate_data
    fleet_mode['cycle_estimate_ts'] = datetime.now(timezone.utc).isoformat()
    with open(FLEET_MODE_PATH, 'w', encoding='utf-8') as f:
        json.dump(fleet_mode, f, indent=2)
    return fleet_mode


def main():
    dry = '--dry' in sys.argv
    est = estimate()
    print(json.dumps(est, indent=2))
    if not dry:
        write_to_fleet_mode(est)
        print(f"\n[written] cycle_estimate -> {FLEET_MODE_PATH}")


if __name__ == '__main__':
    main()
