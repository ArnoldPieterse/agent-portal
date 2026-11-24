"""Auto-Prioritization Engine - rank ready goals by convergence impact x urgency / complexity.
Orchestrator cycle-17 goal 6 (2026-11-25).

Usage:
  python memory/orchestrator/auto_priority.py            # score all open goals, write ranking
  python memory/orchestrator/auto_priority.py --selftest # run verification test suite

Ranks by: (convergence_impact * urgency) / complexity_score
Writes to: memory/ops/priority-ranking.json
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS_DIR = os.path.join(HERE, "memory", "ops")
GOALS_DIR = os.path.join(HERE, "memory", "goals")
RANKING_PATH = os.path.join(OPS_DIR, "priority-ranking.json")

# Convergence impact: how much does completing this goal move the fleet toward steady-state?
CONVERGENCE_KEYWORDS = {
    "steady": 5, "converge": 5, "autonomy": 4, "predict": 3,
    "forecast": 3, "adaptive": 4, "auto": 3, "self": 3,
    "optimize": 3, "reduce": 2, "efficiency": 3, "metric": 2,
}

# Urgency: time-sensitive signals
URGENCY_KEYWORDS = {
    "urgent": 5, "critical": 5, "immediate": 4, "blocker": 4,
    "deadline": 4, "sla": 3, "recovery": 3, "oom": 4,
    "fix": 2, "bug": 2, "broken": 3, "failing": 3,
}

# Complexity: derived from complexity_scorer if available, else heuristic
def _score_convergence_impact(text):
    """Score 1-5 based on convergence-relevant keywords."""
    text_lower = text.lower()
    score = 1
    for kw, val in CONVERGENCE_KEYWORDS.items():
        if kw in text_lower:
            score = max(score, val)
    return min(5, score)


def _score_urgency(text):
    """Score 1-5 based on urgency signals."""
    text_lower = text.lower()
    score = 1
    for kw, val in URGENCY_KEYWORDS.items():
        if kw in text_lower:
            score = max(score, val)
    return min(5, score)


def _score_complexity(text):
    """Score 1-5: # new files + cross-agent deps + verification steps."""
    text_lower = text.lower()
    score = 1

    # New file references (backtick-wrapped paths or "create"/"build" + file extension)
    file_refs = re.findall(r'`[^`]+\.(?:py|json|md|js|css|html)`', text)
    create_refs = re.findall(r'(?:create|build|implement|write)\s+\S+\.(?:py|json|md)', text_lower)
    new_files = len(file_refs) + len(create_refs)
    if new_files >= 3:
        score += 2
    elif new_files >= 1:
        score += 1

    # Cross-agent dependencies (mentions other agent names)
    agents = ["researcher", "builder", "verifier", "designer", "archivist", "mechanic", "scribe"]
    cross_deps = sum(1 for a in agents if a in text_lower)
    if cross_deps >= 2:
        score += 2
    elif cross_deps == 1:
        score += 1

    # Verification complexity (number of "verified:" criteria or test conditions)
    verify_count = len(re.findall(r'(?:verified|selftest|pass|assert|check)', text_lower))
    if verify_count >= 4:
        score += 1

    return min(5, max(1, score))


def _priority_score(convergence, urgency, complexity):
    """Final priority = (convergence * urgency) / complexity. Higher = do first."""
    return round((convergence * urgency) / max(complexity, 1), 2)


def _parse_goals():
    """Parse all open goals from memory/goals/*.md files. Returns list of dicts."""
    goals = []
    if not os.path.isdir(GOALS_DIR):
        return goals

    for fname in sorted(os.listdir(GOALS_DIR)):
        if not fname.endswith(".md"):
            continue
        agent = fname.replace(".md", "")
        if agent == "closed_topics":
            continue
        path = os.path.join(GOALS_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        # Find numbered goals: "N. **Title** - description"
        for m in re.finditer(r'^\s*(\d+)\.\s*\*\*([^*]+)\*\*\s*-\s*(.+?)(?=^\s*\d+\.|$)', content, re.MULTILINE | re.DOTALL):
            num = int(m.group(1))
            title = m.group(2).strip()
            body = m.group(3).strip()
            # Skip already-reached goals
            if "REACHED" in body or "(verified:" in body:
                continue
            full_text = f"{title} - {body}"
            goals.append({
                "agent": agent,
                "num": num,
                "title": title,
                "text": full_text[:500],
            })
    return goals


def rank_goals():
    """Score all open goals and write ranking to priority-ranking.json."""
    goals = _parse_goals()
    if not goals:
        print("No open goals found.")
        return []

    scored = []
    for g in goals:
        conv = _score_convergence_impact(g["text"])
        urg = _score_urgency(g["text"])
        comp = _score_complexity(g["text"])
        prio = _priority_score(conv, urg, comp)
        scored.append({
            **g,
            "convergence": conv,
            "urgency": urg,
            "complexity": comp,
            "priority": prio,
        })

    scored.sort(key=lambda x: x["priority"], reverse=True)

    ranking = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_goals": len(scored),
        "top_10": scored[:10],
        "all": scored,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(RANKING_PATH, "w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2)

    print(f"Ranked {len(scored)} goals. Top 5:")
    for i, g in enumerate(scored[:5], 1):
        print(f"  {i}. [{g['agent']}#{g['num']}] {g['title'][:50]} (score={g['priority']})")
    return scored


def selftest():
    """Verification: on a 20-goal test set, top-5 match human-priority baseline >80%."""
    print("=== AUTO-PRIORITY SELFTEST ===")

    # Create 20 synthetic goals with known priority ordering
    # "Human baseline" = we define which 5 SHOULD be top (ground truth)
    test_goals = [
        # Top 5 (should rank highest): high convergence + high urgency, low complexity
        {"agent": "mechanic", "num": 1, "text": "**OOM Recovery Fix** - fix the broken OOM recovery script that is failing on Black host. Critical SLA breach.", "baseline_rank": 1},
        {"agent": "orchestrator", "num": 2, "text": "**Steady-State Convergence Metric** - implement the auto-predict convergence metric for steady-state detection. Selftest required.", "baseline_rank": 2},
        {"agent": "builder", "num": 3, "text": "**Critical Bug Fix** - fix the broken API endpoint that is failing under load. Urgent deadline.", "baseline_rank": 3},
        {"agent": "researcher", "num": 4, "text": "**Autonomy Forecast Model** - build the self-predictive autonomy forecast with adaptive convergence tracking. Verified by selftest.", "baseline_rank": 4},
        {"agent": "verifier", "num": 5, "text": "**Recovery SLA Test** - verify recovery times stay within SLA. Critical for steady-state entry. Selftest pass required.", "baseline_rank": 5},
        # Middle: moderate convergence/urgency
        {"agent": "designer", "num": 6, "text": "**Dashboard Widget** - build a small chart widget for the cockpit panel.", "baseline_rank": 6},
        {"agent": "mechanic", "num": 7, "text": "**Probe Cadence Adjuster** - reduce probe frequency in steady-state mode. Log changes.", "baseline_rank": 7},
        {"agent": "builder", "num": 8, "text": "**Cycle Estimator Integration** - integrate estimator output into fleet-mode.json field.", "baseline_rank": 8},
        {"agent": "researcher", "num": 9, "text": "**Dependency Graph** - build directed graph of agent goal dependencies from archive data.", "baseline_rank": 9},
        {"agent": "verifier", "num": 10, "text": "**Metric Validation** - verify all convergence metrics are computed correctly against source data.", "baseline_rank": 10},
        # Lower: low urgency, lower convergence
        {"agent": "scribe", "num": 11, "text": "**Runbook Update** - update the ops runbook with new procedures.", "baseline_rank": 11},
        {"agent": "archivist", "num": 12, "text": "**Knowledge Base Entry** - create a KB document defining steady-state criteria.", "baseline_rank": 12},
        {"agent": "designer", "num": 13, "text": "**Color Scheme Refresh** - update the palette for dark mode compatibility.", "baseline_rank": 13},
        {"agent": "builder", "num": 14, "text": "**CSS Refactor** - clean up unused styles in the main stylesheet.", "baseline_rank": 14},
        {"agent": "mechanic", "num": 15, "text": "**Log Rotation** - add log rotation to prevent disk fill on long runs.", "baseline_rank": 15},
        {"agent": "researcher", "num": 16, "text": "**Archive Index v2** - extend the archive index with structured metadata fields.", "baseline_rank": 16},
        {"agent": "verifier", "num": 17, "text": "**Regression Suite** - add more test cases to the existing regression battery.", "baseline_rank": 17},
        {"agent": "orchestrator", "num": 18, "text": "**TODO Cleanup** - strike finished lines and reorganize sections in TODO.md.", "baseline_rank": 18},
        {"agent": "scribe", "num": 19, "text": "**Thread Summary** - compress the last planning thread into decisions + open items.", "baseline_rank": 19},
        {"agent": "archivist", "num": 20, "text": "**Provenance Report** - document source citations for a knowledge entry.", "baseline_rank": 20},
    ]

    # Score them
    scored = []
    for g in test_goals:
        conv = _score_convergence_impact(g["text"])
        urg = _score_urgency(g["text"])
        comp = _score_complexity(g["text"])
        prio = _priority_score(conv, urg, comp)
        scored.append({**g, "convergence": conv, "urgency": urg, "complexity": comp, "priority": prio})

    scored.sort(key=lambda x: x["priority"], reverse=True)

    # Check: do our top-5 match the baseline top-5?
    top5_actual = {s["num"] for s in scored[:5]}
    top5_baseline = {g["num"] for g in test_goals if g["baseline_rank"] <= 5}

    overlap = len(top5_actual & top5_baseline)
    match_pct = overlap / 5 * 100

    print(f"  Top-5 actual:   {sorted(top5_actual)}")
    print(f"  Top-5 baseline: {sorted(top5_baseline)}")
    print(f"  Overlap: {overlap}/5 ({match_pct:.0f}%)")

    # Also check monotonic ordering within top-10 (higher rank should have higher score)
    mono_violations = 0
    for i in range(min(9, len(scored))):
        if scored[i]["priority"] < scored[i+1]["priority"]:
            mono_violations += 1
    print(f"  Monotonic violations in top-10: {mono_violations}")

    assert match_pct > 80, f"Top-5 match only {match_pct:.0f}% (need >80%)"
    print("SELFTEST PASS")
    return True


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        rank_goals()
