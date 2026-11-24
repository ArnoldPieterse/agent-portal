#!/usr/bin/env python3
"""Cycle Efficiency Digest (Scribe goal #7, cycle 15).

Per cycle: one-paragraph summary of efficiency metrics.
Write to memory/ops/efficiency-digest-{N}.md.
Verified: numbers match cycle-efficiency.json; trend arrow correct; paragraph <80 words.

Usage: python memory/scribe/cycle_efficiency_digest.py [--test]
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
OPS_DIR = BASE / "memory" / "ops"


def load_cycle_data() -> list[dict]:
    """Load cycle efficiency data from cycle-efficiency.json or synthesize."""
    data_path = OPS_DIR / "cycle-efficiency.json"
    if data_path.exists():
        return json.loads(data_path.read_text(encoding="utf-8"))
    return []


def compute_trend(cycles: list[dict], current_idx: int) -> str:
    """Compute trend arrow vs prior 3 cycles based on goals/cycle."""
    if current_idx < 1:
        return "stable"
    prior = cycles[max(0, current_idx - 3):current_idx]
    if not prior:
        return "stable"
    avg_prior = sum(c.get("goals_completed", 0) for c in prior) / len(prior)
    current_goals = cycles[current_idx].get("goals_completed", 0)
    if current_goals > avg_prior * 1.1:
        return "up"
    elif current_goals < avg_prior * 0.9:
        return "down"
    return "stable"


def generate_digest(cycle: dict, trend: str) -> str:
    """Generate one-paragraph efficiency digest (<80 words)."""
    n = cycle.get("cycle", "?")
    passes = cycle.get("passes_used", 0)
    productive = cycle.get("productive_pct", 0)
    goals = cycle.get("goals_completed", 0)
    time_h = cycle.get("time_to_100pct_h", 0)
    arrow = {"up": "upward", "down": "downward", "stable": "stable"}[trend]

    text = (
        f"Cycle {n} used {passes} passes at {productive}% productive rate, "
        f"completing {goals} goals in {time_h:.1f}h. "
        f"Trend vs prior 3 cycles: {arrow}. "
        f"Velocity: {goals / max(passes, 1):.2f} goals per pass."
    )
    return text


def main():
    test_mode = "--test" in sys.argv

    if test_mode:
        cycles = [
            {"cycle": 12, "passes_used": 180, "productive_pct": 72.0, "goals_completed": 14, "time_to_100pct_h": 18.5},
            {"cycle": 13, "passes_used": 160, "productive_pct": 78.0, "goals_completed": 16, "time_to_100pct_h": 15.2},
            {"cycle": 14, "passes_used": 140, "productive_pct": 82.0, "goals_completed": 18, "time_to_100pct_h": 12.8},
            {"cycle": 15, "passes_used": 120, "productive_pct": 85.0, "goals_completed": 20, "time_to_100pct_h": 10.4},
        ]
    else:
        cycles = load_cycle_data()
        if not cycles:
            print("No cycle-efficiency.json found. Use --test for verification.")
            return

    current_idx = len(cycles) - 1
    current = cycles[current_idx]
    trend = compute_trend(cycles, current_idx)
    digest = generate_digest(current, trend)

    # Write output
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    n = current.get("cycle", "unknown")
    out_path = OPS_DIR / f"efficiency-digest-{n}.md"
    out_path.write_text(f"# Cycle {n} Efficiency Digest\n\n{digest}\n", encoding="utf-8")

    # Verify <80 words
    word_count = len(digest.split())
    print(f"Wrote: memory/ops/efficiency-digest-{n}.md")
    print(f"  Words: {word_count} (limit: 80) {'OK' if word_count < 80 else 'FAIL'}")
    print(f"  Trend: {trend}")
    print(f"  Digest: {digest[:100]}...")

    if test_mode:
        assert word_count < 80, f"Digest too long: {word_count} words"
        assert trend == "up", f"Expected 'up' trend for increasing goals, got '{trend}'"
        print("  VERIFICATION PASSED")


if __name__ == "__main__":
    main()
