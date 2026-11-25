"""Convergence-Informed Goal Prioritizer.

Reads next10.json candidates + lane progress, re-ranks by convergence impact:
  score = p_reached * (1 - complexity/3) * lane_urgency / hours

lane_urgency = 1 - (done/total): lanes closer to done get higher urgency
because closing their remaining goals moves fleet % faster.

Usage: python memory/orchestrator/goal_prioritizer.py [--top N] [--json]
"""
import json, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # C:\Projects\AgentPortal
NEXT10 = ROOT / "memory" / "goals" / "next10.json"
CALIBRATION = ROOT / "memory" / "goals" / "calibration.json"
AUTONOMY = ROOT / "memory" / "ops" / "autonomy-score.json"


def load_next10():
    return json.loads(NEXT10.read_text(encoding="utf-8"))


def lane_urgency(lanes: dict, agent: str) -> float:
    """1.0 when lane is at 0/10 (most urgent), 0.0 when done."""
    lane = lanes.get(agent, {})
    total = lane.get("total", 10)
    done = lane.get("done", 0)
    if total == 0:
        return 0.0
    return 1.0 - (done / total)


def load_autonomy_trend() -> float:
    """Return autonomy score (0-100); 50 = neutral if file missing."""
    try:
        data = json.loads(AUTONOMY.read_text(encoding="utf-8"))
        return data.get("score", 50.0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 50.0


def convergence_score(card: dict, lanes: dict, autonomy: float = 50.0) -> float:
    """Higher = more valuable for fleet convergence right now.

    Autonomy trend modulates complexity tolerance:
      - autonomy > 70 (improving): relax penalty, accept harder goals
      - autonomy < 50 (degrading): tighten penalty, prefer simple wins
    """
    p = card.get("p_reached", 0.5)
    complexity = card.get("complexity", 1)
    hours = max(card.get("hours", 1.0), 0.1)
    urgency = lane_urgency(lanes, card.get("agent", ""))

    # Base penalty: 1/3 per complexity level above 1
    base_penalty = (complexity - 1) / 3.0
    # Autonomy modifier: +20% tolerance at score 100, -20% at score 0
    autonomy_mod = (autonomy - 50.0) / 100.0 * 0.4  # range [-0.2, +0.2]
    effective_penalty = max(base_penalty - autonomy_mod, 0.0)
    complexity_factor = max(1.0 - effective_penalty, 0.2)

    return round(p * complexity_factor * urgency / hours, 4)


def prioritize(data: dict, top_n: int = 10) -> list:
    lanes = data.get("lanes", {})
    candidates = data.get("next10", [])
    autonomy = load_autonomy_trend()

    scored = []
    for card in candidates:
        s = convergence_score(card, lanes, autonomy)
        scored.append({**card, "convergence_score": s})

    scored.sort(key=lambda x: x["convergence_score"], reverse=True)
    return scored[:top_n]


def main():
    ap = argparse.ArgumentParser(description="Convergence-informed goal prioritizer")
    ap.add_argument("--top", type=int, default=10, help="Show top N goals")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    data = load_next10()
    fleet = data.get("fleet", {})
    ranked = prioritize(data, args.top)

    autonomy = load_autonomy_trend()

    if args.json:
        out = {"fleet": fleet, "autonomy_score": autonomy, "ranked_goals": ranked}
        print(json.dumps(out, indent=2))
    else:
        print(f"Fleet: {fleet.get('done',0)}/{fleet.get('total',0)} ({fleet.get('pct',0):.1f}%)  |  Autonomy: {autonomy:.1f}/100")
        print(f"{'Rank':<5}{'Agent':<14}{'Score':<8}{'P':<7}{'Hrs':<6}{'Goal'}")
        print("-" * 90)
        for i, g in enumerate(ranked, 1):
            title = g.get("title", g.get("goal", ""))[:40]
            print(f"{i:<5}{g['agent']:<14}{g['convergence_score']:<8.4f}"
                  f"{g.get('p_reached',0):<7.2f}{g.get('hours',0):<6.1f}{title}")


if __name__ == "__main__":
    main()
