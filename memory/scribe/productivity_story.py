#!/usr/bin/env python3
"""Productivity Story (Weekly) - Scribe goal #4, cycle 15.

Generates a weekly narrative (5-8 sentences) on fleet productivity evolution:
what changed, which agents improved/declined, what interventions helped.

Usage: python memory/scribe/productivity_story.py [--simulate]
Output: memory/synthesis/productivity-week-{ISO}.md
"""
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
OPS_DIR = BASE / "memory" / "ops"
SYNTH_DIR = BASE / "memory" / "synthesis"
AGENTS = ["orchestrator", "researcher", "verifier", "scribe",
          "designer", "builder", "archivist", "mechanic"]


def _load_daily_data(days=7):
    """Load productivity data from daily baseline files or autoloop.jsonl."""
    data = defaultdict(lambda: defaultdict(float))  # data[agent][date] = rate

    # Try daily baseline files first
    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        f = OPS_DIR / f"productivity-baseline-{d}.json"
        if f.exists():
            try:
                content = json.loads(f.read_text(encoding="utf-8"))
                for agent, metrics in content.items():
                    if isinstance(metrics, dict) and "rate" in metrics:
                        data[agent][d] = metrics["rate"]
            except (json.JSONDecodeError, KeyError):
                pass

    # Fallback: scan autoloop.jsonl
    al = OPS_DIR / "autoloop.jsonl"
    if al.exists() and not any(data.values()):
        for line in al.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                agent = rec.get("agent", "")
                ts = rec.get("ts", "")[:10]
                productive = rec.get("productive", False)
                if agent and ts:
                    data[agent][ts + "_total"] += 1
                    if productive:
                        data[agent][ts + "_prod"] += 1
            except json.JSONDecodeError:
                pass
        # Convert counts to rates
        for agent in list(data.keys()):
            for date_key in [k for k in data[agent] if k.endswith("_total")]:
                d = date_key[:-6]
                total = data[agent][date_key]
                prod = data[agent].get(d + "_prod", 0)
                data[agent][d] = (prod / total * 100) if total > 0 else 0
                del data[agent][date_key]
                data[agent].pop(d + "_prod", None)

    return data


def _simulate_data(days=7, trend="improving"):
    """Generate synthetic 7-day data with known trend for testing."""
    random.seed(42)
    data = defaultdict(dict)
    base_rates = {a: random.uniform(30, 60) for a in AGENTS}

    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        for agent in AGENTS:
            if trend == "improving":
                rate = base_rates[agent] + i * 3 + random.uniform(-5, 5)
            elif trend == "declining":
                rate = base_rates[agent] - i * 3 + random.uniform(-5, 5)
            else:
                rate = base_rates[agent] + random.uniform(-10, 10)
            data[agent][d] = max(0, min(100, rate))

    # Save to files for traceability
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    for agent in AGENTS:
        for d, rate in data[agent].items():
            f = OPS_DIR / f"productivity-baseline-{d}.json"
            existing = {}
            if f.exists():
                try:
                    existing = json.loads(f.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
            existing[agent] = {"rate": round(rate, 1), "source": "simulated"}
            f.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    return data


def generate_story(data):
    """Generate 5-8 sentence productivity narrative."""
    if not any(data.values()):
        return "No productivity data available for this period."

    dates = sorted(set(d for agent_data in data.values() for d in agent_data))
    if len(dates) < 2:
        return "Insufficient data (need at least 2 days) to generate trend narrative."

    first_date, last_date = dates[0], dates[-1]

    # Compute per-agent trends
    agent_trends = {}
    for agent in AGENTS:
        if agent not in data or len(data[agent]) < 2:
            continue
        vals = [data[agent][d] for d in sorted(data[agent].keys())]
        first_val, last_val = vals[0], vals[-1]
        delta = last_val - first_val
        agent_trends[agent] = {
            "first": round(first_val, 1),
            "last": round(last_val, 1),
            "delta": round(delta, 1),
            "direction": "improved" if delta > 5 else ("declined" if delta < -5 else "stable"),
        }

    # Overall trend
    all_first = [t["first"] for t in agent_trends.values()]
    all_last = [t["last"] for t in agent_trends.values()]
    overall_first = sum(all_first) / len(all_first) if all_first else 0
    overall_last = sum(all_last) / len(all_last) if all_last else 0
    overall_delta = overall_last - overall_first
    overall_dir = "improved" if overall_delta > 5 else ("declined" if overall_delta < -5 else "held steady")

    # Top improvers and decliners
    sorted_agents = sorted(agent_trends.items(), key=lambda x: x[1]["delta"], reverse=True)
    top_improvers = [(a, t) for a, t in sorted_agents[:3] if t["delta"] > 5]
    top_decliners = [(a, t) for a, t in sorted_agents[-3:] if t["delta"] < -5]

    # Build narrative (5-8 sentences)
    sentences = []
    sentences.append(
        f"Over the period {first_date} to {last_date}, fleet-wide productivity {overall_dir} "
        f"from {overall_first:.0f}% to {overall_last:.0f}% ({overall_delta:+.1f}pp)."
    )

    if top_improvers:
        names = ", ".join(f"{a} ({t['delta']:+.0f}pp)" for a, t in top_improvers)
        sentences.append(f"Strongest gains came from {names}.")

    if top_decliners:
        names = ", ".join(f"{a} ({t['delta']:+.0f}pp)" for a, t in top_decliners)
        sentences.append(f"Declines were seen in {names}, suggesting possible resource contention or task mismatch.")

    stable = [a for a, t in agent_trends.items() if t["direction"] == "stable"]
    if stable:
        sentences.append(f"{len(stable)} agents ({', '.join(stable[:4])}) held steady within the noise band.")

    # Best and worst single-day
    best_agent_day = max(
        ((a, d, data[a][d]) for a in AGENTS for d in data.get(a, {})),
        key=lambda x: x[2], default=None
    )
    if best_agent_day:
        sentences.append(
            f"Peak performance was {best_agent_day[0]} at {best_agent_day[2]:.0f}% on {best_agent_day[1]}."
        )

    # Intervention suggestion
    avg_rate = sum(d["fleet_wide"] for d in data) / len(data) * 100
    sentences.append(f"Average weekly productivity was {avg_rate:.0f}%, with a range of {min(d['fleet_wide'] for d in data)*100:.0f}\u2013{max(d['fleet_wide'] for d in data)*100:.0f}% across the seven days.")
    if overall_dir == "improved":
        sentences.append("Current dispatch strategy appears effective; maintain current mode rotation cadence.")
    elif overall_dir == "declined":
        sentences.append("Recommend reviewing idle-task assignment quality and checking for model-load degradation on affected hosts.")
    else:
        sentences.append("Fleet is in equilibrium; no intervention needed this cycle.")

    return " ".join(sentences)


def main():
    simulate = "--simulate" in sys.argv
    if simulate:
        data = _simulate_data(days=7, trend="improving")
        print("[simulate] generated 7 days of improving-trend data")
    else:
        data = _load_daily_data(days=7)

    story = generate_story(data)

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    out_path = SYNTH_DIR / f"productivity-week-{iso_week}.md"
    out_path.write_text(f"# Productivity Story {iso_week}\n\n{story}\n", encoding="utf-8")

    print(f"[productivity_story] wrote {out_path.relative_to(BASE)} ({len(story)} chars, {story.count(chr(46)) + 1} sentences)")
    print(f"  {story[:200]}...")


if __name__ == "__main__":
    main()
