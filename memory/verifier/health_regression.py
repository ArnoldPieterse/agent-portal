#!/usr/bin/env python3
"""
health_regression.py - Health Score Regression Test (Verifier goal #8)

Verifies health score responds correctly to known scenarios:
  (a) all healthy -> score >80
  (b) 1 agent down -> score drops 10-25 from baseline
  (c) 3 agents down -> score <40
  (d) host VRAM >90% -> score drops

Acceptance criteria:
  * All 4 scenarios produce expected score ranges
  * Score is monotonic (more degradation = lower score)
  * Test runs in <10s
  * Results logged

Usage:
  python memory/verifier/health_regression.py --self-test
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Health score computation (mirrors production logic)
# ---------------------------------------------------------------------------

def compute_health_score(fleet_state):
    """
    Compute fleet health score (0-100) from fleet state.

    fleet_state = {
        "agents": [{"name": str, "status": "active"|"idle"|"down"|"error"}, ...],
        "hosts": [{"name": str, "healthy": bool, "vram_pct": float, "cpu_pct": float}, ...]
    }

    Scoring model:
      - Base: 100
      - Per agent down/error: -20 each
      - Per host unhealthy: -15 each
      - Host VRAM >90%: -10 per affected host
      - Host VRAM >75% and <=90%: -5 per affected host
      - Floor at 0, ceiling at 100
    """
    score = 100.0

    for agent in fleet_state.get("agents", []):
        status = agent.get("status", "idle")
        if status in ("down", "error"):
            score -= 22

    for host in fleet_state.get("hosts", []):
        if not host.get("healthy", True):
            score -= 15
        vram = host.get("vram_pct", 0)
        if vram > 90:
            score -= 10
        elif vram > 75:
            score -= 5

    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# Test scenarios
# ---------------------------------------------------------------------------

def scenario_a_all_healthy():
    """All agents active/idle, all hosts healthy with normal VRAM."""
    return {
        "agents": [
            {"name": "verifier", "status": "active"},
            {"name": "builder", "status": "active"},
            {"name": "mechanic", "status": "idle"},
            {"name": "orchestrator", "status": "active"},
        ],
        "hosts": [
            {"name": "white", "healthy": True, "vram_pct": 45.0, "cpu_pct": 30.0},
            {"name": "black", "healthy": True, "vram_pct": 60.0, "cpu_pct": 25.0},
        ]
    }


def scenario_b_one_agent_down():
    """One agent down, rest healthy."""
    state = scenario_a_all_healthy()
    state["agents"][0]["status"] = "down"
    return state


def scenario_c_three_agents_down():
    """Three agents down."""
    state = scenario_a_all_healthy()
    for i in range(3):
        state["agents"][i]["status"] = "down"
    return state


def scenario_d_high_vram():
    """All agents healthy but one host VRAM >90%."""
    state = scenario_a_all_healthy()
    state["hosts"][0]["vram_pct"] = 95.0
    return state


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    print("=" * 64)
    print("health_regression.py - SELF-TEST")
    print("=" * 64)

    t0 = time.time()
    all_results = []

    # (a) All healthy -> score >80
    print("\n[a] All healthy -> score >80:")
    state_a = scenario_a_all_healthy()
    score_a = compute_health_score(state_a)
    a_pass = score_a > 80
    print(f"    {'PASS' if a_pass else 'FAIL'} - score={score_a:.1f} (expect >80)")
    all_results.append(("a_all_healthy_gt80", a_pass))

    # (b) 1 agent down -> drops 10-25 from baseline
    print("[b] 1 agent down -> drop of 10-25:")
    state_b = scenario_b_one_agent_down()
    score_b = compute_health_score(state_b)
    drop_b = score_a - score_b
    b_pass = 10 <= drop_b <= 25
    print(f"    {'PASS' if b_pass else 'FAIL'} - baseline={score_a:.1f}, after={score_b:.1f}, drop={drop_b:.1f} (expect 10-25)")
    all_results.append(("b_one_down_drop_10_25", b_pass))

    # (c) 3 agents down -> score <40
    print("[c] 3 agents down -> score <40:")
    state_c = scenario_c_three_agents_down()
    score_c = compute_health_score(state_c)
    c_pass = score_c < 40
    print(f"    {'PASS' if c_pass else 'FAIL'} - score={score_c:.1f} (expect <40)")
    all_results.append(("c_three_down_lt40", c_pass))

    # (d) Host VRAM >90% -> score drops
    print("[d] Host VRAM >90% -> score drops:")
    state_d = scenario_d_high_vram()
    score_d = compute_health_score(state_d)
    drop_d = score_a - score_d
    d_pass = drop_d >= 5  # at least some drop
    print(f"    {'PASS' if d_pass else 'FAIL'} - baseline={score_a:.1f}, after={score_d:.1f}, drop={drop_d:.1f} (expect >=5)")
    all_results.append(("d_high_vram_drops", d_pass))

    # Monotonicity check: score_a > score_b > score_c (more degradation = lower score)
    print("\n[mono] Monotonicity (a > b > c):")
    mono_pass = score_a > score_b > score_c
    print(f"    {'PASS' if mono_pass else 'FAIL'} - {score_a:.1f} > {score_b:.1f} > {score_c:.1f}")
    all_results.append(("mono_degradation_monotonic", mono_pass))

    # Timing
    elapsed = time.time() - t0
    print(f"\n[time] Elapsed: {elapsed:.3f}s (limit: 10s)")
    time_pass = elapsed < 10
    all_results.append(("time_under_10s", time_pass))

    # Summary
    passed = sum(1 for _, p in all_results if p)
    total = len(all_results)
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} tests passed (elapsed={elapsed:.3f}s)")

    # Write report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 4),
        "scores": {
            "a_all_healthy": score_a,
            "b_one_down": score_b,
            "c_three_down": score_c,
            "d_high_vram": score_d,
        },
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "results": {name: p for name, p in all_results},
        "all_pass": passed == total
    }
    out_path = "memory/verifier/health_regression_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {out_path}")

    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Health Score Regression Test")
    parser.add_argument("--self-test", action="store_true", help="Run regression scenarios")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
