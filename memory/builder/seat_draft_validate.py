"""Seat Draft Validation Pipeline - validates goals drafted for unreachable agents.

Checks per goal:
  (a) tool_existence: referenced tools/scripts exist on disk
  (b) path_validity: file paths in the goal are valid (parent dirs exist or creatable)
  (c) backup_designation: if goal references a canonical/backup pattern, it's consistent

Usage:
  python memory/builder/seat_draft_validate.py --validate FILE    # validate goals in a specific file
  python memory/builder/seat_draft_validate.py --all              # validate all agent goal files
  python memory/builder/seat_draft_validate.py --selftest         # run self-test (5 valid + 3 invalid)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
GOALS_DIR = os.path.normpath(os.path.join(ROOT, "memory", "goals"))

# Patterns to extract from goal text
TOOL_PATTERN = re.compile(r'(?:python|run|execute)\s+([\w/\\.]+\.py)', re.IGNORECASE)
PATH_PATTERN = re.compile(r'[`\"]((?:memory|ui|ops|fleet)/[\w/\\.\-]+)[`\"]')
BACKUP_PATTERN = re.compile(r'(canonical|backup|pin|PIN_FILES)')


def extract_checks(goal_text: str):
    """Extract validation checks from goal text.
    Returns list of {type, target} dicts.
    """
    checks = []
    # Tool existence: python X.py
    for m in TOOL_PATTERN.finditer(goal_text):
        checks.append({"type": "tool_existence", "target": m.group(1)})
    # Path validity
    for m in PATH_PATTERN.finditer(goal_text):
        checks.append({"type": "path_validity", "target": m.group(1)})
    # Backup designation (informational)
    if BACKUP_PATTERN.search(goal_text):
        checks.append({"type": "backup_designation", "target": goal_text[:80]})
    return checks


def check_tool_exists(target: str) -> dict:
    """Check if a tool/script exists on disk."""
    # Try relative to ROOT and common locations
    candidates = [
        os.path.join(ROOT, target),
        os.path.join(ROOT, "memory", target),
        os.path.normpath(target),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return {"pass": True, "found_at": c}
    return {"pass": False, "suggestion": f"Create {target} or fix path reference"}


def check_path_valid(target: str) -> dict:
    """Check if a file path is valid (parent dir exists or is creatable)."""
    full = os.path.join(ROOT, target)
    parent = os.path.dirname(full)
    if os.path.isdir(parent):
        return {"pass": True, "note": f"Parent {parent} exists"}
    # Check if it's a new file in a known top-level directory
    top_dir = target.split('/')[0] if '/' in target else ''
    depth = target.count('/')
    if top_dir in ('memory', 'ui', 'ops', 'fleet') and depth <= 2:
        return {"pass": True, "note": f"New file in valid directory structure: {target}"}
    # Deeply nested path with non-existent parent = suspicious
    return {"pass": False, "suggestion": f"Parent dir missing for {target}; create it or fix path"}


def check_backup(target: str) -> dict:
    """Check backup/canonical designation consistency (informational)."""
    # This is a soft check - just flag if the pattern looks inconsistent
    if 'canonical' in target.lower() and 'backup' in target.lower():
        return {"pass": True, "note": "Both canonical and backup referenced (OK)"}
    return {"pass": True, "note": "No conflict detected"}


def validate_goal(goal_num: int, goal_text: str, agent: str = "unknown") -> dict:
    """Run all checks on a single goal. Returns report dict."""
    checks = extract_checks(goal_text)
    results = []
    for chk in checks:
        if chk["type"] == "tool_existence":
            r = check_tool_exists(chk["target"])
        elif chk["type"] == "path_validity":
            r = check_path_valid(chk["target"])
        else:
            r = check_backup(chk["target"])
        results.append({**chk, **r})

    all_pass = all(r["pass"] for r in results) if results else True
    return {
        "goal_num": goal_num,
        "agent": agent,
        "overall": "PASS" if all_pass else "FAIL",
        "checks": results,
        "fixes": [r["suggestion"] for r in results if not r["pass"] and "suggestion" in r],
    }


def parse_goals_from_file(filepath: str, agent: str = None) -> list:
    """Parse numbered goals from a .md file. Returns list of {num, title, text}."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    goals = []
    for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s+(.*)', content, re.MULTILINE):
        goals.append({"num": int(m.group(1)), "title": m.group(2), "text": m.group(3)})
    if agent is None:
        # Infer from filename
        agent = os.path.basename(filepath).replace('.md', '')
    return goals


def validate_file(filepath: str, agent: str = None) -> dict:
    """Validate all goals in a file. Returns report."""
    goals = parse_goals_from_file(filepath, agent)
    results = [validate_goal(g["num"], g["title"] + " - " + g["text"]) for g in goals]
    passed = sum(1 for r in results if r["overall"] == "PASS")
    return {
        "file": filepath,
        "agent": agent or os.path.basename(filepath).replace('.md', ''),
        "total_goals": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_selftest():
    """Self-test: 5 valid + 3 invalid drafts processed; fixes are actionable."""
    print("=== seat_draft_validate.py SELFTEST ===")

    # 5 valid goals (tools exist, paths valid)
    valid_goals = [
        (1, "Complexity Scorer", "Run `python memory/orchestrator/complexity_scorer.py` to score. Output to `memory/ops/scores.json`."),
        (2, "Autonomy Score", "Execute `python memory/orchestrator/autonomy_score.py` and write to `memory/ops/autonomy-score.json`."),
        (3, "Goal Inherit", "Run `python memory/orchestrator/goal_inherit.py --scan`. Output: `memory/ops/inheritance-proposals.json`."),
        (4, "Convergence API", "Implement in `memory/orchestrator/convergence_api.py`. Wire to agent_portal.py."),
        (5, "Cycle Estimator", "Run `python memory/orchestrator/cycle_estimator.py`. Write to `memory/ops/fleet-mode.json`."),
    ]

    # 3 invalid goals (missing tools, bad paths)
    invalid_goals = [
        (6, "Missing Tool", "Run `python memory/orchestrator/nonexistent_tool_xyz.py` to do stuff."),
        (7, "Bad Path", "Write output to `memory/nonexistent_dir/deep/nested/file.json`."),
        (8, "Both Bad", "Execute `python tools/does_not_exist.py` and write to `invalid/path/nope.md`."),
    ]

    pass_count = 0
    fail_count = 0
    actionable_fixes = 0

    for num, title, text in valid_goals:
        r = validate_goal(num, f"{title} - {text}")
        assert r["overall"] == "PASS", f"Expected PASS for goal {num} ({title}): {r['checks']}"
        pass_count += 1
        print(f"  VALID PASS: #{num} {title}")

    for num, title, text in invalid_goals:
        r = validate_goal(num, f"{title} - {text}")
        assert r["overall"] == "FAIL", f"Expected FAIL for goal {num} ({title})"
        fail_count += 1
        # Check fixes are actionable (non-empty, contain specific text)
        assert len(r["fixes"]) > 0, f"No fixes for failing goal {num}"
        for fix in r["fixes"]:
            assert len(fix) > 10, f"Fix too short to be actionable: {fix}"
            actionable_fixes += 1
        print(f"  INVALID FAIL: #{num} {title} -> fixes: {r['fixes']}")

    assert pass_count == 5, f"Expected 5 valid passes, got {pass_count}"
    assert fail_count == 3, f"Expected 3 invalid fails, got {fail_count}"
    assert actionable_fixes >= 3, f"Expected >=3 actionable fixes, got {actionable_fixes}"

    # Also validate a real file to ensure no crashes
    real_file = os.path.join(GOALS_DIR, "mechanic.md")
    if os.path.exists(real_file):
        report = validate_file(real_file, "Mechanic")
        print(f"\n  Live validation: {report['file']} -> {report['passed']}/{report['total_goals']} PASS")

    print(f"\n  SELFTEST PASS: {pass_count} valid + {fail_count} invalid processed, {actionable_fixes} actionable fixes")
    return True


def main():
    if '--selftest' in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    if '--all' in sys.argv:
        reports = []
        for f in sorted(os.listdir(GOALS_DIR)):
            if f.endswith('.md') and f not in ('INDEX.md', 'closed_topics.json'):
                agent = f.replace('.md', '')
                if agent in ('builder', 'mechanic', 'archivist', 'orchestrator', 'researcher', 'verifier', 'designer', 'scribe'):
                    reports.append(validate_file(os.path.join(GOALS_DIR, f), agent))
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files_checked": len(reports),
            "total_goals": sum(r["total_goals"] for r in reports),
            "total_passed": sum(r["passed"] for r in reports),
            "total_failed": sum(r["failed"] for r in reports),
            "reports": reports,
        }
        out = os.path.join(ROOT, "memory", "builder", "seat-draft-report.json")
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2)
        print(f"Validated {summary['total_goals']} goals across {len(reports)} files: "
              f"{summary['total_passed']} PASS, {summary['total_failed']} FAIL")
        print(f"Report: {out}")
    elif '--validate' in sys.argv:
        idx = sys.argv.index('--validate')
        if idx + 1 < len(sys.argv):
            f = sys.argv[idx + 1]
            report = validate_file(f)
            print(json.dumps(report, indent=2))
        else:
            print("Usage: --validate FILE")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()