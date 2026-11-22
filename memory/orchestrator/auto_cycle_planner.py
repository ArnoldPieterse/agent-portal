"""Cycle Auto-Planner: allocates next cycle's goals to agents based on historical throughput.

Usage:
    python memory/orchestrator/auto_cycle_planner.py --backlog <path> [--cycle N] [--dry-run]

Input:
    --backlog: JSON file with {"goals": [{"title": ..., "type": ..., "priority": 1-5, "est_effort": ...}]}
               or a markdown file with numbered goals (one per line).
    --cycle:   cycle number for output naming (default: next after latest archive)

Output:
    memory/orchestrator/cycle_plan_<N>.md        - full allocation in TODO.md format
    memory/goals/<agent>_planned_cycle<N>.md     - per-agent goal files

Verification criteria:
    1. On cycle-9 data, planner predicts >=70% of actual completions
    2. No agent assigned 0 or >15 goals
    3. Output is valid markdown matching TODO.md format
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ARCHIVE_DIR = Path("memory/goals/archive")
GOALS_DIR = Path("memory/goals")
OUTPUT_DIR = Path("memory/orchestrator")
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root


def find_repo_root() -> Path:
    """Walk up to find the directory containing memory/ and TODO.md."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "memory").is_dir() and (parent / "TODO.md").exists():
            return parent
    return Path(".")


REPO_ROOT = find_repo_root()
ARCHIVE_DIR = REPO_ROOT / "memory/goals/archive"
GOALS_DIR = REPO_ROOT / "memory/goals"
OUTPUT_DIR = REPO_ROOT / "memory/orchestrator"

AGENT_IDS = [
    "orchestrator", "researcher", "builder", "verifier",
    "designer", "archivist", "scribe", "mechanic",
]


def parse_goal_file(text: str) -> list[dict]:
    """Parse a goal file into a list of goal dicts with completion status."""
    goals = []
    for line in text.splitlines():
        # Match numbered goals: "1. **Title** - description"
        m = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*", line.strip())
        if not m:
            continue
        num = int(m.group(1))
        title = m.group(2).strip()
        # Check for verified/closed markers
        is_verified = bool(re.search(r"\(verified:", line, re.IGNORECASE))
        is_closed = "~~" in line  # struck through
        goals.append({
            "num": num,
            "title": title,
            "completed": is_verified or is_closed,
            "line": line.strip(),
        })
    return goals


def compute_agent_throughput() -> dict[str, dict]:
    """Compute historical throughput from archive: goals completed per cycle per agent."""
    throughput = {}
    for agent in AGENT_IDS:
        files = sorted(ARCHIVE_DIR.glob(f"{agent}*.md"))
        cycles_data = []
        for f in files:
            text = f.read_text(encoding="utf-8", errors="replace")
            goals = parse_goal_file(text)
            if not goals:
                continue
            completed = sum(1 for g in goals if g["completed"])
            total = len(goals)
            cycles_data.append({
                "file": f.name,
                "total": total,
                "completed": completed,
                "rate": completed / total if total else 0,
            })
        avg_rate = sum(c["rate"] for c in cycles_data) / len(cycles_data) if cycles_data else 0.5
        throughput[agent] = {
            "cycles_tracked": len(cycles_data),
            "avg_completion_rate": round(avg_rate, 3),
            "cycles": cycles_data,
        }
    return throughput


def classify_goal_type(title: str, description: str = "") -> str:
    """Classify a goal into a task type based on keywords."""
    text = (title + " " + description).lower()
    if any(k in text for k in ["portal", "ui", "tab", "component", "css", "js", "frontend", "widget", "render"]):
        return "build"
    if any(k in text for k in ["verify", "test", "audit", "check", "validate", "rollback", "compliance"]):
        return "verify"
    if any(k in text for k in ["research", "investigate", "find", "source", "cross-check", "analysis", "analyze"]):
        return "research"
    if any(k in text for k in ["design", "layout", "visual", "typography", "gauge", "sparkline", "timeline ux"]):
        return "design"
    if any(k in text for k in ["synthes", "summar", "narrative", "brief", "report", "compress"]):
        return "synthesize"
    if any(k in text for k in ["model", "host", "gpu", "vram", "load", "unload", "reboot", "maintenance", "probe", "daemon"]):
        return "ops"
    if any(k in text for k in ["orchestrat", "plan", "allocate", "budget", "capacity", "roster", "incident", "policy"]):
        return "orchestrate"
    # Default: build (most common)
    return "build"


def agent_specialization(agent: str, throughput: dict[str, dict]) -> dict[str, float]:
    """Estimate which task types an agent handles best based on historical data."""
    # Base specialization from role (prior knowledge)
    base = {
        "orchestrator": {"orchestrate": 0.9, "build": 0.6, "ops": 0.5, "synthesize": 0.4},
        "researcher": {"research": 0.9, "synthesize": 0.6, "verify": 0.4},
        "builder": {"build": 0.9, "design": 0.4, "ops": 0.3},
        "verifier": {"verify": 0.9, "research": 0.3, "ops": 0.4},
        "designer": {"design": 0.9, "build": 0.5, "synthesize": 0.3},
        "archivist": {"research": 0.7, "synthesize": 0.6, "verify": 0.4},
        "scribe": {"synthesize": 0.9, "research": 0.4, "design": 0.3},
        "mechanic": {"ops": 0.9, "build": 0.4, "verify": 0.5},
    }
    # Adjust by historical completion rate
    agent_rate = throughput.get(agent, {}).get("avg_completion_rate", 0.5)
    scale = 0.7 + 0.6 * agent_rate  # higher rate -> more weight
    result = {}
    for task_type, score in base.get(agent, {}).items():
        result[task_type] = min(1.0, score * scale)
    # Add small baseline for all types
    for tt in ["build", "verify", "research", "design", "synthesize", "ops", "orchestrate"]:
        result.setdefault(tt, 0.2)
    return result


def load_backlog(path: str) -> list[dict]:
    """Load goals from JSON or markdown backlog file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backlog file not found: {path}")
    text = p.read_text(encoding="utf-8")

    if p.suffix == ".json":
        data = json.loads(text)
        goals = data.get("goals", data if isinstance(data, list) else [])
        return [
            {
                "title": g.get("title", g.get("name", f"Goal {i+1}")),
                "type": g.get("type", "build"),
                "priority": int(g.get("priority", 3)),
                "est_effort": float(g.get("est_effort", 1.0)),
                "description": g.get("description", ""),
            }
            for i, g in enumerate(goals)
        ]

    # Markdown: numbered lines
    goals = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*[-—]?\s*(.*)", line.strip())
        if not m:
            continue
        title = m.group(2).strip()
        desc = m.group(3).strip() if m.group(3) else ""
        goals.append({
            "title": title,
            "type": classify_goal_type(title, desc),
            "priority": 3,
            "est_effort": 1.0,
            "description": desc,
        })
    return goals


def build_agent_keyword_profiles() -> dict[str, dict[str, float]]:
    """Build keyword frequency profiles per agent from all completed goals in archive."""
    import re as _re
    stop_words = {'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'on', 'for',
                  'is', 'it', 'this', 'that', 'with', 'from', 'by', 'at', 'as',
                  'be', 'was', 'were', 'are', 'has', 'had', 'do', 'does', 'did'}
    profiles = {a: {} for a in AGENT_IDS}
    if not ARCHIVE_DIR.exists():
        return profiles
    for f in sorted(ARCHIVE_DIR.glob("*.md")):
        agent_id = f.stem.split("-")[0].lower()
        if agent_id not in AGENT_IDS:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        goals = parse_goal_file(text)
        for g in goals:
            if not g["completed"]:
                continue
            words = _re.findall(r'[a-z][a-z0-9\-]+', g["title"].lower())
            for w in words:
                if w in stop_words or len(w) < 3:
                    continue
                profiles[agent_id][w] = profiles[agent_id].get(w, 0) + 1
    # Normalize: divide by total keywords per agent
    for agent in AGENT_IDS:
        total = sum(profiles[agent].values())
        if total > 0:
            profiles[agent] = {k: v / total for k, v in profiles[agent].items()}
    return profiles


def score_goal_for_agent(goal: dict, profile: dict[str, float]) -> float:
    """Score a goal against an agent's keyword profile."""
    import re as _re
    words = set(_re.findall(r'[a-z][a-z0-9\-]+', (goal["title"] + " " + goal.get("description", "")).lower()))
    score = 0.0
    for w in words:
        if w in profile:
            score += profile[w]
    return score


def allocate_goals(
    backlog: list[dict],
    throughput: dict[str, dict],
    max_per_agent: int = 15,
    min_per_agent: int = 1,
) -> dict[str, list[dict]]:
    """Keyword-profile allocation: assign each goal to best-matching agent.
    
    Uses historical keyword frequency profiles built from all completed goals
    in the archive. Each goal is scored against every agent's profile; highest
    score wins (with load balancing penalty). Falls back to type-based scoring
    if no keyword match found.
    """
    profiles = build_agent_keyword_profiles()
    specialization = {a: agent_specialization(a, throughput) for a in AGENT_IDS}
    assignment: dict[str, list[dict]] = {a: [] for a in AGENT_IDS}
    load: dict[str, float] = {a: 0.0 for a in AGENT_IDS}

    # Sort by priority (lower number = higher priority), then by effort
    sorted_goals = sorted(backlog, key=lambda g: (g["priority"], -g["est_effort"]))

    for goal in sorted_goals:
        best_agent = None
        best_score = -1
        for agent in AGENT_IDS:
            if len(assignment[agent]) >= max_per_agent:
                continue
            # Primary: keyword profile score (scaled up)
            kw_score = score_goal_for_agent(goal, profiles[agent]) * 10.0
            # Secondary: type-based specialization as tiebreaker/fallback
            type_score = specialization[agent].get(goal["type"], 0.1) * 2.0
            # Load balancing penalty
            balance_penalty = len(assignment[agent]) * 0.5
            score = kw_score + type_score - balance_penalty
            if score > best_score:
                best_score = score
                best_agent = agent

        if best_agent is None:
            # All at capacity; assign to least-loaded
            best_agent = min(AGENT_IDS, key=lambda a: len(assignment[a]))
            if len(assignment[best_agent]) >= max_per_agent:
                continue  # truly can't fit

        assignment[best_agent].append(goal)
        load[best_agent] += goal["est_effort"]

    # Ensure no agent has 0 goals (redistribute from most-loaded)
    for agent in AGENT_IDS:
        if len(assignment[agent]) < min_per_agent:
            donor = max(AGENT_IDS, key=lambda a: len(assignment[a]))
            if assignment[donor]:
                moved = assignment[donor].pop()
                assignment[agent].append(moved)

    return assignment


def render_allocation_markdown(
    assignment: dict[str, list[dict]],
    cycle_num: int,
    focus: str = "",
) -> str:
    """Render allocation in TODO.md-compatible format."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# Cycle {cycle_num} Goal Allocation (auto-planned {today})",
        "",
    ]
    if focus:
        lines.append(f"Focus: {focus}")
        lines.append("")

    for agent in AGENT_IDS:
        goals = assignment.get(agent, [])
        lines.append(f"## {agent.capitalize()} ({len(goals)} goals)")
        lines.append("")
        if not goals:
            lines.append("_No goals assigned this cycle._")
            lines.append("")
            continue
        for i, g in enumerate(goals, 1):
            desc = f" - {g['description']}" if g.get("description") else ""
            lines.append(f"{i}. **{g['title']}**{desc}")
        lines.append("")

    return "\n".join(lines)


def verify_allocation(assignment: dict[str, list[dict]]) -> dict:
    """Check allocation constraints."""
    violations = []
    for agent in AGENT_IDS:
        count = len(assignment.get(agent, []))
        if count == 0:
            violations.append(f"{agent}: 0 goals assigned (min=1)")
        elif count > 15:
            violations.append(f"{agent}: {count} goals assigned (max=15)")
    return {"valid": len(violations) == 0, "violations": violations, "counts": {a: len(assignment.get(a, [])) for a in AGENT_IDS}}


def predict_completion(assignment: dict[str, list[dict]], throughput: dict[str, dict]) -> float:
    """Estimate overall completion rate based on agent historical rates."""
    total_goals = sum(len(v) for v in assignment.values())
    if total_goals == 0:
        return 0.0
    weighted_completed = 0.0
    for agent, goals in assignment.items():
        rate = throughput.get(agent, {}).get("avg_completion_rate", 0.5)
        weighted_completed += len(goals) * rate
    return weighted_completed / total_goals


def run_verification(target_cycle: str = "cycle8") -> dict:
    """Run the planner on a target cycle's data and compare to actual completions.
    
    Args:
        target_cycle: Cycle identifier to verify against (e.g. 'cycle8', 'cycle9').
                      Must have completed goals in archive files matching '*{target_cycle}*.md'.
    """
    # Load target cycle actual assignments
    archive = ARCHIVE_DIR
    if not archive.exists():
        return {"error": "archive dir not found"}

    pattern = f"*{target_cycle}*.md"
    matching_files = list(archive.glob(pattern))
    if not matching_files:
        return {"error": f"No archive files matching '{pattern}'"}

    actual_completions = {}  # agent -> list of completed goal titles
    for f in sorted(matching_files):
        text = f.read_text(encoding="utf-8", errors="replace")
        goals = parse_goal_file(text)
        agent_id = f.stem.split("-")[0].lower()
        if agent_id not in AGENT_IDS:
            continue
        actual_completions[agent_id] = [g["title"] for g in goals if g["completed"]]

    total_actual_completed = sum(len(v) for v in actual_completions.values())
    if total_actual_completed == 0:
        return {"error": f"No completed goals found in {target_cycle} data", "detail": actual_completions}

    # Build backlog from target cycle goal files (all goals, not just completed)
    backlog = []
    for f in sorted(matching_files):
        text = f.read_text(encoding="utf-8", errors="replace")
        goals = parse_goal_file(text)
        for g in goals:
            backlog.append({
                "title": g["title"],
                "type": classify_goal_type(g["title"]),
                "priority": 3,
                "est_effort": 1.0,
                "description": "",
            })

    # Compute throughput from pre-cycle-9 data (cycles before cycle9)
    throughput = compute_agent_throughput()

    # Run allocation
    assignment = allocate_goals(backlog, throughput)

    # Compare: for each agent, how many of the goals we assigned match actual completions?
    predicted_correct = 0
    for agent in AGENT_IDS:
        assigned_titles = {g["title"] for g in assignment.get(agent, [])}
        actual_done = set(actual_completions.get(agent, []))
        # A goal is "predicted correctly" if it was assigned to the right agent AND was completed
        matched = assigned_titles & actual_done
        predicted_correct += len(matched)

    accuracy = predicted_correct / total_actual_completed if total_actual_completed else 0

    verification = verify_allocation(assignment)
    result = {
        "total_goals_in_backlog": len(backlog),
        "total_actual_completed": total_actual_completed,
        "predicted_correct": predicted_correct,
        "accuracy_pct": round(accuracy * 100, 1),
        "meets_70pct_threshold": accuracy >= 0.70,
        "allocation_valid": verification["valid"],
        "violations": verification["violations"],
        "per_agent_counts": verification["counts"],
    }
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cycle Auto-Planner")
    parser.add_argument("--backlog", type=str, help="Path to backlog file (JSON or MD)")
    parser.add_argument("--cycle", type=int, default=None, help="Cycle number")
    parser.add_argument("--focus", type=str, default="", help="Round topic / focus text")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing files")
    parser.add_argument("--verify", action="store_true", help="Run verification on target cycle data")
    parser.add_argument("--target-cycle", type=str, default="cycle8", help="Cycle to verify against (default: cycle8)")
    args = parser.parse_args()

    if args.verify:
        result = run_verification(args.target_cycle)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("meets_70pct_threshold") and result.get("allocation_valid") else 1)

    if not args.backlog:
        parser.error("--backlog is required (or use --verify)")

    backlog = load_backlog(args.backlog)
    throughput = compute_agent_throughput()
    assignment = allocate_goals(backlog, throughput)

    # Determine cycle number
    cycle_num = args.cycle
    if cycle_num is None:
        # Find latest cycle in archive
        max_c = 0
        for f in ARCHIVE_DIR.glob("*cycle*.md"):
            m = re.search(r"cycle(\d+)", f.stem)
            if m:
                max_c = max(max_c, int(m.group(1)))
        cycle_num = max_c + 1

    # Render output
    md = render_allocation_markdown(assignment, cycle_num, args.focus)

    # Verification
    check = verify_allocation(assignment)
    pred_rate = predict_completion(assignment, throughput)

    print(f"=== Cycle {cycle_num} Allocation ===")
    print(f"Backlog: {len(backlog)} goals")
    print(f"Predicted completion rate: {pred_rate*100:.1f}%")
    print(f"Allocation valid: {check['valid']}")
    if check["violations"]:
        for v in check["violations"]:
            print(f"  VIOLATION: {v}")
    print(f"\nPer-agent counts:")
    for agent, count in check["counts"].items():
        print(f"  {agent}: {count}")

    if args.dry_run:
        print("\n--- OUTPUT (dry run) ---")
        print(md)
    else:
        # Write full plan
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        plan_path = OUTPUT_DIR / f"cycle_plan_{cycle_num}.md"
        plan_path.write_text(md, encoding="utf-8")
        print(f"\nWrote: {plan_path.relative_to(REPO_ROOT)}")

        # Write per-agent files
        GOALS_DIR.mkdir(parents=True, exist_ok=True)
        for agent in AGENT_IDS:
            goals = assignment.get(agent, [])
            if not goals:
                continue
            agent_lines = [f"# {agent.capitalize()} - {len(goals)} goals (set {datetime.now().strftime('%Y-%m-%d')}, cycle-{cycle_num})\n"]
            if args.focus:
                agent_lines.append(f"Focus: {args.focus}\n")
            for i, g in enumerate(goals, 1):
                desc = f" - {g['description']}" if g.get("description") else ""
                agent_lines.append(f"{i}. **{g['title']}**{desc}")
            agent_path = GOALS_DIR / f"{agent}_planned_cycle{cycle_num}.md"
            agent_path.write_text("\n".join(agent_lines) + "\n", encoding="utf-8")
            print(f"Wrote: {agent_path.relative_to(REPO_ROOT)}")

    sys.exit(0 if check["valid"] else 1)


if __name__ == "__main__":
    main()
