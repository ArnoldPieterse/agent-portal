"""seat_draft_check.py - Validate executability of seat-drafted goals.

For goals drafted on behalf of unreachable seats, checks:
  A. Referenced file paths / tools exist (or are creatable in the agent's own lane)
  B. Verification criteria are automatable without the seat online >24h
  C. A backup agent is designated and has capacity (not already at 10/10 goals reached)

Usage:
    python memory/verifier/seat_draft_check.py          # run against real seat-drafted goal files
    python memory/verifier/seat_draft_check.py --selftest  # synthetic test cases

Output: memory/verifier/seat_draft_check_report.json
"""
import pathlib, json, re, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
GOALS_DIR = MEM / "goals"
REPORT = MEM / "verifier" / "seat_draft_check_report.json"

# Seats that are currently unreachable (per model load status)
UNREACHABLE_SEATS = {"archivist", "scribe"}

# Map of which agent can back up which seat (designated backups)
BACKUP_MAP = {
    "archivist": ["researcher", "verifier"],
    "scribe": ["researcher", "orchestrator"],
}


def load_goal_file(seat: str) -> list:
    """Parse a seat's goal file into structured entries."""
    path = GOALS_DIR / f"{seat}.md"
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    goals = []
    # Match numbered goals: "1. **Title** - body..."
    goal_pat = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*[-\u2013\u2014]\s+(.+?)(?=\n\d+\.|\Z)", re.MULTILINE | re.DOTALL)
    for m in goal_pat.finditer(content):
        num = int(m.group(1))
        title = m.group(2).strip()
        body = m.group(3).strip()
        # Check if reached/closed
        is_reached = "[REACHED" in body or "\u2705 REACHED" in body or "(verified:" in body
        goals.append({"num": num, "title": title, "body": body, "reached": is_reached})
    return goals


def check_paths_exist(body: str) -> tuple:
    """Check that referenced file paths in the goal body exist or are in a creatable location.
    
    For output/create targets (paths after 'Output:' or 'create'), only require the
    top-level lane directory to exist. For input references, require the path or its
    parent to exist.
    """
    # Separate output paths from input paths
    output_paths = set(re.findall(r"(?:output|Output)\s*:\s*((?:memory|ui)/[\w\-/\.]+)", body))
    create_paths = set(re.findall(r"create\s+((?:memory|ui)/[\w\-/\.]+)", body, re.IGNORECASE))
    all_known = output_paths | create_paths
    
    # Extract ALL file path references
    path_refs = re.findall(r"(?:memory|ui)/[\w\-/\.]+", body)
    missing = []
    for ref in path_refs:
        p = MEM.parent / ref if not ref.startswith("memory/") else MEM.parent / ref
        if p.exists():
            continue  # exists, fine
        if ref in all_known:
            # It's an output/create target - only require top-level dir to exist
            top_dir = MEM.parent / ref.split("/")[0]
            if not top_dir.exists():
                missing.append(ref)
            continue
        # Input path: require parent exists (file can be created) or file exists
        parent = p.parent
        if not parent.exists():
            missing.append(ref)
    return len(missing) == 0, missing


def check_automatable(body: str) -> tuple:
    """Check that verification criteria don't require the seat to be online.

    Rules:
    - If body references 'output:' with a file path -> automatable (write a file)
    - If body references 'verified:' or 'self-test' -> automatable
    - If body requires interactive session, live queries from that seat's model,
      or human judgment -> NOT automatable
    """
    # Positive indicators of automatability
    auto_indicators = [
        r"output\s*:",           # explicit output file
        r"verified\s*:",          # explicit verification criteria
        r"self-test",             # self-test mentioned
        r"\d+\s*(valid|invalid)", # classification counts
    ]
    # Negative indicators (require live seat)
    manual_indicators = [
        r"requires?\s+human\s+judgment",
        r"interactive\s+session",
        r"live\s+query.*seat",
        r"must\s+be\s+run\s+on\s+(archivist|scribe)",
    ]

    has_auto = any(re.search(ind, body, re.IGNORECASE) for ind in auto_indicators)
    has_manual = any(re.search(ind, body, re.IGNORECASE) for ind in manual_indicators)

    if has_manual:
        return False, "requires live seat interaction"
    if has_auto:
        return True, "automatable (output file + verification criteria present)"
    # Default: if it writes a file or checks something, assume automatable
    if re.search(r"(create|write|build|compile|document|store|track)", body, re.IGNORECASE):
        return True, "action implies file output (assumed automatable)"
    return False, "no clear automatable verification criteria"


def check_backup_available(seat: str) -> tuple:
    """Check that at least one backup agent exists and isn't at 10/10 goals reached."""
    backups = BACKUP_MAP.get(seat, [])
    available = []
    for bak in backups:
        goal_file = GOALS_DIR / f"{bak}.md"
        if not goal_file.exists():
            continue
        content = goal_file.read_text(encoding="utf-8")
        reached_count = len(re.findall(r"REACHED|\u2705\s*REACHED", content))
        total_goals = len(re.findall(r"^\d+\.\s+\*\*", content, re.MULTILINE))
        # If not all goals are reached, backup has capacity
        if reached_count < total_goals:
            available.append(bak)
    return len(available) > 0, available


def validate_goal(seat: str, goal: dict) -> dict:
    """Run all three checks on a single goal. Returns pass/fail + details."""
    body = f"{goal['title']} {goal['body']}"

    paths_ok, missing_paths = check_paths_exist(body)
    auto_ok, auto_reason = check_automatable(goal["body"])
    backup_ok, available_backups = check_backup_available(seat)

    executable = paths_ok and auto_ok and backup_ok

    return {
        "seat": seat,
        "goal_num": goal["num"],
        "title": goal["title"],
        "reached": goal["reached"],
        "executable": executable,
        "checks": {
            "paths_exist": paths_ok,
            "missing_paths": missing_paths,
            "automatable": auto_ok,
            "auto_reason": auto_reason,
            "backup_available": backup_ok,
            "available_backups": available_backups,
        }
    }


def run_real() -> dict:
    """Run against actual seat-drafted goal files."""
    results = []
    for seat in sorted(UNREACHABLE_SEATS):
        goals = load_goal_file(seat)
        for g in goals:
            if not g["reached"]:  # only check open goals
                results.append(validate_goal(seat, g))

    executable_count = sum(1 for r in results if r["executable"])
    non_executable_count = len(results) - executable_count

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "real",
        "seats_checked": sorted(UNREACHABLE_SEATS),
        "total_open_goals": len(results),
        "executable": executable_count,
        "non_executable": non_executable_count,
        "results": results,
    }
    return report


def run_selftest() -> dict:
    """Run synthetic test cases: 5 valid + 3 invalid."""
    # Synthetic goals for testing
    test_goals_valid = [
        {"num": 1, "title": "Write Report", "body": "create memory/test/report.md with summary. Output: memory/test/report.md. Verified: file exists and >100 bytes.", "reached": False},
        {"num": 2, "title": "Index Files", "body": "build index of all .md files in memory/. Output: memory/index.json. Verified: count matches actual file count.", "reached": False},
        {"num": 3, "title": "Track Metrics", "body": "track daily metrics to memory/metrics.jsonl. Output: memory/metrics.jsonl. Verified: 7+ entries present.", "reached": False},
        {"num": 4, "title": "Validate Schema", "body": "validate all JSON files in memory/ops/ against schema. self-test: 5 valid + 3 invalid classified correctly. Output: memory/schema-report.json.", "reached": False},
        {"num": 5, "title": "Compile Patterns", "body": "compile pattern reports into memory/patterns.md. Deduplicate entries. Verified: no duplicate titles; all source files cited.", "reached": False},
    ]
    test_goals_invalid = [
        {"num": 6, "title": "Live Query", "body": "requires human judgment to evaluate quality of responses. Must be run on archivist seat directly.", "reached": False},
        {"num": 7, "title": "Missing Input Dep", "body": "read data from memory/ghost/tool_output.json and transform it. Output: memory/result.md. Verified: result matches source.", "reached": False},
        {"num": 8, "title": "No Verification", "body": "do some analysis and figure out what to do next.", "reached": False},
    ]

    results = []
    # Test valid goals (should all be executable)
    for g in test_goals_valid:
        r = validate_goal("archivist", g)
        results.append({**r, "expected": True})
    # Test invalid goals (should all be non-executable)
    for g in test_goals_invalid:
        r = validate_goal("archivist", g)
        results.append({**r, "expected": False})

    passed = sum(1 for r in results if r["executable"] == r["expected"])
    total = len(results)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "selftest",
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "verdict": "PASS" if passed == total else "FAIL",
        "results": results,
    }


def main():
    if "--selftest" in sys.argv:
        report = run_selftest()
        print(f"Self-test: {report['passed']}/{report['total_cases']} PASS ({report['verdict']})")
        for r in report["results"]:
            status = "OK" if r["executable"] == r["expected"] else "MISMATCH"
            print(f"  [{status}] #{r['goal_num']} {r['title']}: executable={r['executable']} expected={r['expected']}")
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        sys.exit(0 if report["verdict"] == "PASS" else 1)
    else:
        report = run_real()
        print(f"Real check: {report['executable']}/{report['total_open_goals']} executable goals for unreachable seats")
        for r in report["results"]:
            flag = "OK" if r["executable"] else "FAIL"
            issues = []
            if not r["checks"]["paths_exist"]:
                issues.append(f"missing paths: {r['checks']['missing_paths']}")
            if not r["checks"]["automatable"]:
                issues.append(r["checks"]["auto_reason"])
            if not r["checks"]["backup_available"]:
                issues.append("no backup with capacity")
            issue_str = "; ".join(issues) if issues else ""
            print(f"  [{flag}] {r['seat']} #{r['goal_num']} {r['title']}: {issue_str}")
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        sys.exit(0)


if __name__ == "__main__":
    main()
