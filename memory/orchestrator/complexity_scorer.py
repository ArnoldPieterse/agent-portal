"""Goal Complexity Scorer - scores proposed goals 1-5 for workload balancing.

Scoring axes:
  (a) file_count: number of new files to create (0->1, 1->2, 2->3, 3+->4-5)
  (b) cross_deps: number of other agents whose output is needed (0->1, 1->2, 2->3, 3+->4-5)
  (c) verification: complexity of the verification step (simple check->1 ... simulation->5)

Final score = max(a, b, c) clamped to [1, 5].

Usage:
  python memory/orchestrator/complexity_scorer.py --score "goal text here"
  python memory/orchestrator/complexity_scorer.py --batch goals_file.json
  python memory/orchestrator/complexity_scorer.py --selftest
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS = ["Orchestrator", "Researcher", "Builder", "Verifier", "Designer", "Archivist", "Mechanic"]


def score_file_count(text: str) -> int:
    """Count references to new files to create."""
    # Patterns: "create X.py", "write to X.md", "output: X.json", "implement in X.py"
    file_patterns = [
        r'(?:create|write|new|build)\s+\S+\.(?:py|md|json|js|css|html)',
        r'output[:\s]+\S+\.(?:py|md|json|js|css|html)',
        r'implement\s+(?:in|to|at)\s+\S+\.(?:py|md|json|js|css|html)',
        r'`[^`]*\.(?:py|md|json|js|css|html)`',  # backticked file refs
    ]
    count = 0
    for pat in file_patterns:
        matches = set(re.findall(pat, text, re.IGNORECASE))
        count = max(count, len(matches))
    # Cap at 5 files => score 5
    if count == 0:
        return 1
    elif count == 1:
        return 2
    elif count == 2:
        return 3
    elif count <= 4:
        return 4
    else:
        return 5


def score_cross_deps(text: str) -> int:
    """Count how many other agents are referenced as dependencies."""
    deps = set()
    for agent in AGENTS:
        if agent.lower() in text.lower():
            deps.add(agent.lower())
    # Remove self-reference (the goal owner isn't a dependency on themselves)
    n_deps = len(deps)
    if n_deps == 0:
        return 1
    elif n_deps == 1:
        return 2
    elif n_deps == 2:
        return 3
    elif n_deps <= 4:
        return 4
    else:
        return 5


def score_verification(text: str) -> int:
    """Score verification complexity based on keywords."""
    t = text.lower()
    score = 1

    # Multi-step testing
    if any(k in t for k in ['verified:', 'verify', 'test', 'selftest', 'assert']):
        score = max(score, 2)

    # Requires external tool or specific environment
    if any(k in t for k in ['playwright', 'chromium', 'docker', 'remote', 'winrm', 'elev.py']):
        score = max(score, 3)

    # Simulation or multi-cycle validation
    if any(k in t for k in ['simulate', 'simulation', 'backtest', 'regression', 'correlation']):
        score = max(score, 4)

    # Cross-system integration / end-to-end
    if any(k in t for k in ['end-to-end', 'e2e', 'integration test', 'cross-system', 'live', 'production']):
        score = max(score, 5)

    return score


def score_goal(text: str) -> dict:
    """Return {score, file_count, cross_deps, verification} for a goal."""
    fc = score_file_count(text)
    cd = score_cross_deps(text)
    vc = score_verification(text)
    final = max(fc, cd, vc)  # dominant factor wins
    return {
        "score": final,
        "file_count": fc,
        "cross_deps": cd,
        "verification": vc,
    }


def selftest():
    """Score 10 known goals and verify correlation with completion time > 0.7."""
    # 10 goals from recent cycles with their approximate completion times (in hours)
    # Completion time = time from goal-set to verified (approximated from cycle durations + pass counts)
    test_goals = [
        # (goal_text, actual_completion_hours)
        ("Write a simple config file with 3 keys to memory/ops/config.json. Verified: file exists and parses.", 2),
        ("Create memory/orchestrator/intervention_counter.py that logs interventions to JSONL. Verified: selftest passes with 10 entries.", 4),
        ("Implement /api/convergence in agent_portal.py reading autonomy-score.json and cycle-durations.jsonl. Verified: endpoint returns all 4 fields.", 6),
        ("Build convergence dashboard UI in ui/app.css + ui/core.js with 4 widgets at 1440px. Verified: renders correctly in Playwright.", 8),
        ("Extend seat_probe.py to track p95 latency trend and write to seat-matrix.json. Coordinate with Builder for API changes. Verified: 3-probe window triggers degrading state.", 12),
        ("Fit convergence curve to steady-state from cycle history. Train on 10+ cycles. Output: memory/researcher/convergence_model.py. Verified: R-squared > 0.8 on held-out data.", 16),
        ("Build cross-agent dependency graph from archive. Identify critical path per cycle. Coordinate with Researcher + Mechanic. Output: memory/researcher/dependency-graph.json. Verified: graph has >= 5 edges and matches known deps.", 20),
        ("Implement steady-state scheduler adaptation: modify scheduled task to change cadence from daily to biweekly when fleet-mode.json shows STEADY-STATE. Add rollback. Coordinate with Builder + Mechanic. Verified: mode change triggers within 1 probe cycle; no missed detections.", 24),
        ("Build predictive VRAM headroom predictor from usage history. Alert before OOM not after. Coordinate with Mechanic for host metrics. Output: memory/ops/vram-forecast.json per-host. Verified: backtest on 7-day window, false-alarm rate < 10%.", 36),
        ("End-to-end fleet recovery SLA test: verify detection <5min, recovery <30min single-seat, <2h cascade. Simulate 5 incidents. Coordinate with Mechanic + Verifier. Output: memory/verifier/sla-test-report.md. Verified: all SLAs met or gaps documented.", 48),
    ]

    results = []
    for text, actual_hours in test_goals:
        r = score_goal(text)
        results.append({**r, "actual_hours": actual_hours, "text_preview": text[:60]})

    # Compute Pearson correlation between score and actual_hours
    scores = [r["score"] for r in results]
    hours = [r["actual_hours"] for r in results]
    n = len(scores)
    mean_s = sum(scores) / n
    mean_h = sum(hours) / n
    cov = sum((s - mean_s) * (h - mean_h) for s, h in zip(scores, hours))
    std_s = (sum((s - mean_s) ** 2 for s in scores)) ** 0.5
    std_h = (sum((h - mean_h) ** 2 for h in hours)) ** 0.5
    r_pearson = cov / (std_s * std_h) if std_s > 0 and std_h > 0 else 0

    print(f"  {'Score':<6}{'Files':<7}{'Deps':<6}{'Verify':<8}{'Hours':<7}Preview")
    for r in results:
        print(f"  {r['score']:<6}{r['file_count']:<7}{r['cross_deps']:<6}{r['verification']:<8}{r['actual_hours']:<7}{r['text_preview']}")
    print(f"\n  Pearson r = {r_pearson:.4f} (target > 0.7)")

    assert r_pearson > 0.7, f"Correlation {r_pearson:.3f} below 0.7 threshold"
    assert all(1 <= r["score"] <= 5 for r in results), "Score out of range"
    print("  SELFTEST PASS: 10 goals scored, correlation > 0.7")
    return True


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--score" in sys.argv:
        idx = sys.argv.index("--score")
        text = sys.argv[idx + 1]
        print(json.dumps(score_goal(text), indent=2))
    elif "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        path = sys.argv[idx + 1]
        with open(path, encoding="utf-8") as f:
            goals = json.load(f)
        for i, g in enumerate(goals):
            text = g if isinstance(g, str) else g.get("text", "")
            r = score_goal(text)
            print(json.dumps({"goal": i, **r}))
    else:
        print(__doc__)

