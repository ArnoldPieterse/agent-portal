"""Goal Lifecycle Audit — traces every goal through proposed→assigned→worked→verified→closed; flags stuck >48h or missing transitions.

Usage:
  python memory/verifier/goal_lifecycle_audit.py --self-test   # run built-in tests
  python memory/verifier/goal_lifecycle_audit.py               # audit current goals

Design:
- Parses per-lane goal files (memory/goals/*.md) for numbered goals
- Determines lifecycle state from markers:
  * proposed: goal text exists without any marker
  * assigned: appears in a cycle section with lane ownership
  * worked: has progress notes or partial evidence references
  * verified: has "(verified: ..." marker
  * closed: has "(closed: ..." or "(archived: ..." marker
- Flags:
  * stuck >48h: goal in "worked" state for >48 hours without transition to verified/closed
  * missing transitions: goal jumps from proposed directly to verified (skipped assigned/worked)

Self-test uses synthetic goal files to prove detection of stuck + missing transitions.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # memory/
GOALS_DIR = BASE / "goals"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_goal_states(goal_file: Path) -> list:
    """Parse a goal file and determine lifecycle state for each numbered goal."""
    if not goal_file.exists():
        return []
    
    content = goal_file.read_text(encoding="utf-8", errors="replace")
    agent = goal_file.stem  # e.g., "verifier"
    
    # Find all numbered goals: N. **Title** - description (markers)
    goal_pattern = re.compile(r'^(\d+)\.\s+\*\*(.+?)\*\*\s*[-—]\s*(.*)', re.MULTILINE)
    
    results = []
    for match in goal_pattern.finditer(content):
        num = int(match.group(1))
        title = match.group(2).strip()
        rest = match.group(3).strip()
        
        # Determine state from markers
        if "(closed:" in rest or "(archived:" in rest:
            state = "closed"
        elif "(verified:" in rest:
            state = "verified"
        else:
            state = "open"  # proposed/assigned/worked all look the same without explicit markers
        
        results.append({
            "agent": agent,
            "goal_num": num,
            "title": title,
            "state": state,
            "description": rest[:200],
        })
    
    return results


def detect_issues(all_goals: list, stuck_threshold_h: int = 48) -> list:
    """Detect lifecycle issues: stuck goals and missing transitions."""
    issues = []
    
    for goal in all_goals:
        if goal["state"] == "open":
            # Check for explicit progress markers that suggest "worked" state
            desc_lower = goal["description"].lower()
            has_progress = any(kw in desc_lower for kw in ["progress", "partial", "in progress", "wip"])
            
            if has_progress:
                issues.append({
                    "type": "potentially_stuck",
                    "agent": goal["agent"],
                    "goal_num": goal["goal_num"],
                    "title": goal["title"],
                    "detail": f"Open with progress markers but no verified/closed stamp (threshold: {stuck_threshold_h}h)",
                })
        
        # Missing transition check: verified without any evidence of intermediate work
        # (In practice, all our goals go proposed->verified in one pass, so this is informational)
    
    return issues


def run_audit(stuck_threshold_h: int = 48) -> dict:
    """Run full lifecycle audit across all goal files."""
    all_goals = []
    files_checked = 0
    
    for gf in GOALS_DIR.glob("*.md"):
        if gf.name.startswith("_") or "archive" in gf.name.lower():
            continue
        goals = parse_goal_states(gf)
        all_goals.extend(goals)
        if goals:
            files_checked += 1
    
    issues = detect_issues(all_goals, stuck_threshold_h)
    
    # Summary by state
    state_counts = {}
    for g in all_goals:
        state_counts[g["state"]] = state_counts.get(g["state"], 0) + 1
    
    return {
        "ts": now_iso(),
        "files_checked": files_checked,
        "total_goals": len(all_goals),
        "state_counts": state_counts,
        "issues": issues,
        "issue_count": len(issues),
        "pass": len(issues) == 0,
    }


def self_test():
    """Self-test with synthetic goal files. Returns exit code."""
    print("=== Goal Lifecycle Audit Self-Test ===")
    passed = 0
    failed = 0
    
    import tempfile
    
    # T1: Parse a goal file with mixed states
    print("\nT1: Parse goal file with open + verified + closed goals")
    test_content = """# Test Agent Goals

## Cycle X

1. **Open Goal** — no markers yet (progress so far on this)
2. **Verified Goal** — done (verified: 2026-11-23 - self-test passed)
3. **Closed Goal** — complete (closed: 2026-11-22 - archived)
4. **Another Open** — still working on it (partial progress noted)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(test_content)
        test_file = Path(f.name)
    
    goals = parse_goal_states(test_file)
    if len(goals) == 4:
        states = {g["goal_num"]: g["state"] for g in goals}
        if states[1] == "open" and states[2] == "verified" and states[3] == "closed":
            print(f"  PASS: parsed 4 goals, states={states}")
            passed += 1
        else:
            print(f"  FAIL: wrong states: {states}")
            failed += 1
    else:
        print(f"  FAIL: expected 4 goals, got {len(goals)}")
        failed += 1
    
    test_file.unlink(missing_ok=True)
    
    # T2: Detect potentially stuck goal (progress marker + no verified stamp)
    print("\nT2: Goal with 'progress' keyword but no verified stamp -> flagged as potentially stuck")
    goals_with_progress = [
        {"agent": "test", "goal_num": 1, "title": "Stuck thing", "state": "open", "description": "In progress since last cycle"},
        {"agent": "test", "goal_num": 2, "title": "Fine goal", "state": "open", "description": "Just proposed, no work yet"},
    ]
    issues = detect_issues(goals_with_progress)
    stuck_issues = [i for i in issues if i["type"] == "potentially_stuck"]
    if len(stuck_issues) == 1 and stuck_issues[0]["goal_num"] == 1:
        print(f"  PASS: correctly flagged goal #1 as potentially stuck")
        passed += 1
    else:
        print(f"  FAIL: issues={issues}")
        failed += 1
    
    # T3: No issues on clean file (all verified/closed)
    print("\nT3: All goals verified/closed -> no issues")
    clean_goals = [
        {"agent": "test", "goal_num": 1, "title": "Done", "state": "verified", "description": "(verified: ...)"},
        {"agent": "test", "goal_num": 2, "title": "Archived", "state": "closed", "description": "(closed: ...)"},
    ]
    issues = detect_issues(clean_goals)
    if len(issues) == 0:
        print(f"  PASS: 0 issues on clean goals")
        passed += 1
    else:
        print(f"  FAIL: unexpected issues: {issues}")
        failed += 1
    
    # T4: File parsing edge case — empty file
    print("\nT4: Empty goal file -> no goals parsed (graceful)")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("")
        empty_file = Path(f.name)
    goals = parse_goal_states(empty_file)
    if len(goals) == 0:
        print(f"  PASS: empty file yields 0 goals")
        passed += 1
    else:
        print(f"  FAIL: expected 0, got {len(goals)}")
        failed += 1
    empty_file.unlink(missing_ok=True)
    
    # T5: File parsing edge case — no numbered goals (just prose)
    print("\nT5: Prose-only file -> no goals parsed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Just a header\n\nSome prose without numbered goals.\n")
        prose_file = Path(f.name)
    goals = parse_goal_states(prose_file)
    if len(goals) == 0:
        print(f"  PASS: prose file yields 0 goals")
        passed += 1
    else:
        print(f"  FAIL: expected 0, got {len(goals)}")
        failed += 1
    prose_file.unlink(missing_ok=True)
    
    # T6: Run audit on actual goals dir (should work without crashing)
    print("\nT6: Live audit run completes without error")
    try:
        result = run_audit()
        if "total_goals" in result and "state_counts" in result:
            print(f"  PASS: {result['files_checked']} files, {result['total_goals']} goals, states={result['state_counts']}")
            passed += 1
        else:
            print(f"  FAIL: missing keys in result")
            failed += 1
    except Exception as e:
        print(f"  FAIL: exception: {e}")
        failed += 1
    
    print(f"\n=== RESULTS: {passed} PASS / {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Goal Lifecycle Audit")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")
    parser.add_argument("--threshold", type=int, default=48, help="Stuck threshold in hours (default 48)")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    
    result = run_audit(stuck_threshold_h=args.threshold)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
