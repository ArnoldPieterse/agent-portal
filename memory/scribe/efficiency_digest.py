#!/usr/bin/env python3
"""efficiency_digest.py — generate per-cycle efficiency digest (Scribe Goal #7).

Reads pass-budget.json, productivity-baseline.json, and goal files to compute:
  passes used, productive %, goals/cycle, time-to-100%, trend arrow vs prior 3 cycles.
Writes: memory/ops/efficiency-digest-{N}.md (one paragraph, <80 words)
Also writes: memory/ops/cycle-efficiency.json (machine-readable source of truth)

Usage: python memory/scribe/efficiency_digest.py [--cycle N] [--simulate]
"""
import json, sys, os, re, datetime, pathlib

BUDGET = pathlib.Path("memory/ops/pass-budget.json")
BASELINE = pathlib.Path("memory/ops/productivity-baseline.json")
GOALS_DIR = pathlib.Path("memory/goals")
OUT_DIR = pathlib.Path("memory/ops")
EFF_JSON = OUT_DIR / "cycle-efficiency.json"


def count_verified_goals():
    """Count goals with (verified: markers across the 8 agent goal files."""
    AGENTS = {"orchestrator", "researcher", "verifier", "scribe",
              "designer", "builder", "archivist", "mechanic"}
    total = 0
    per_agent = {}
    if not GOALS_DIR.exists():
        return total, per_agent
    for f in sorted(GOALS_DIR.iterdir()):
        if f.stem not in AGENTS:
            continue
        content = f.read_text(encoding='utf-8')
        count = len(re.findall(r'\(verified:', content))
        if count:
            per_agent[f.stem] = count
            total += count
    return total, per_agent


def get_prior_cycles(current_cycle):
    """Read prior efficiency digests to compute trend."""
    priors = []
    for n in range(current_cycle - 1, max(0, current_cycle - 4), -1):
        p = OUT_DIR / f"efficiency-digest-{n}.md"
        if p.exists():
            text = p.read_text(encoding='utf-8')
            # Extract goals count and passes from the text
            m_goals = re.search(r'(\d+)\s+goals', text)
            m_passes = re.search(r'(\d+)\s+passes', text)
            priors.append({
                'cycle': n,
                'goals': int(m_goals.group(1)) if m_goals else None,
                'passes': int(m_passes.group(1)) if m_passes else None
            })
    return priors


def compute_trend(current_goals, priors):
    """Return trend arrow: up/down/stable/insufficient."""
    prior_goals = [p['goals'] for p in priors if p['goals'] is not None]
    if len(prior_goals) < 1:
        return "insufficient history (no prior digests)"
    avg_prior = sum(prior_goals) / len(prior_goals)
    if current_goals > avg_prior * 1.1:
        return "upward ↑"
    elif current_goals < avg_prior * 0.9:
        return "downward ↓"
    else:
        return "stable →"


def main():
    cycle = 15
    simulate = False
    if '--cycle' in sys.argv:
        idx = sys.argv.index('--cycle')
        if idx + 1 < len(sys.argv):
            cycle = int(sys.argv[idx + 1])
    if '--simulate' in sys.argv:
        simulate = True

    # Gather data
    passes_used = 0
    budget_total = 200
    if BUDGET.exists():
        bdata = json.loads(BUDGET.read_text(encoding='utf-8'))
        passes_used = bdata.get('used', 0)
        budget_total = bdata.get('total', 200)

    productive_pct = None
    if BASELINE.exists():
        pdata = json.loads(BASELINE.read_text(encoding='utf-8'))
        total_p = sum(v.get('total_passes', 0) for v in pdata.values() if isinstance(v, dict))
        prod_p = sum(v.get('productive_passes', 0) for v in pdata.values() if isinstance(v, dict))
        if total_p > 0:
            productive_pct = round(100.0 * prod_p / total_p, 1)

    goals_total, per_agent = count_verified_goals()

    # Time-to-100%: approximate from pass data (not precisely trackable without timestamps)
    time_to_100 = None  # hours; null if not determinable

    if simulate:
        passes_used = 120
        productive_pct = 85.0
        goals_total = 20
        time_to_100 = 10.4

    trend = compute_trend(goals_total, get_prior_cycles(cycle))

    # Build the paragraph (<80 words)
    parts = []
    parts.append(f"Cycle {cycle} used {passes_used} passes at "
                 f"{productive_pct if productive_pct is not None else 'N/A'}% productive rate, "
                 f"completing {goals_total} goals")
    if time_to_100:
        parts.append(f"in {time_to_100}h")
    parts.append(f". Trend vs prior 3 cycles: {trend}. "
                 f"Velocity: {round(goals_total / max(passes_used, 1), 2)} goals per pass.")
    paragraph = ''.join(parts)

    # Word count check
    wc = len(paragraph.split())
    if wc > 80:
        paragraph = f"Cycle {cycle}: {passes_used} passes, {productive_pct}% productive, " \
                    f"{goals_total} goals. Trend: {trend}. Velocity: {round(goals_total/max(passes_used,1),2)} goals/pass."

    # Write markdown digest
    md_path = OUT_DIR / f"efficiency-digest-{cycle}.md"
    md_content = f"# Cycle {cycle} Efficiency Digest\n\n{paragraph}\n"
    md_path.write_text(md_content, encoding='utf-8')
    print(f"[efficiency_digest] wrote {md_path} ({len(paragraph.split())} words)")

    # Write machine-readable JSON (source of truth for verification)
    eff_data = {
        "cycle": cycle,
        "passes_used": passes_used,
        "budget_total": budget_total,
        "productive_pct": productive_pct,
        "goals_completed": goals_total,
        "goals_per_agent": per_agent,
        "time_to_100_h": time_to_100,
        "trend": trend,
        "velocity_goals_per_pass": round(goals_total / max(passes_used, 1), 4),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    EFF_JSON.write_text(json.dumps(eff_data, indent=2), encoding='utf-8')
    print(f"[efficiency_digest] wrote {EFF_JSON}")

    return 0


if __name__ == "__main__":
    sys.exit(main())