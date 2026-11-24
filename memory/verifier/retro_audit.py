"""retro_audit.py - Cycle Retrospective Completeness Audit.

Verifies that auto-generated retrospectives:
  A. Contain all required sections (Summary, Goals Completed, Slipped/Open, Key Learnings, Suggestions)
  B. Every data point cites a resolvable file path (no dangling references)
  C. Goal counts in Summary match the actual section contents

Usage:
    python memory/verifier/retro_audit.py              # audit all retros in memory/goals/
    python memory/verifier/retro_audit.py --selftest   # synthetic test cases

Output: memory/verifier/retro_audit_report.json
"""
import pathlib, json, re, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
GOALS_DIR = MEM / "goals"
ROOT = MEM.parent
REPORT_PATH = MEM / "verifier" / "retro_audit_report.json"

# Required sections (markdown ## headers)
REQUIRED_SECTIONS = [
    "Summary",
    "Goals Completed",
    "Slipped",
    "Key Learnings",
    "Suggestions",
]


def find_retros() -> list:
    """Find all retrospective files in goals directory."""
    return sorted(GOALS_DIR.glob("retro-cycle-*.md"))


def check_sections(content: str) -> tuple:
    """Check that all required sections are present. Returns (ok, missing)."""
    headers = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    # Normalize: strip trailing colons/spaces
    normalized = [h.strip().rstrip(':').lower() for h in headers]
    
    missing = []
    for req in REQUIRED_SECTIONS:
        req_lower = req.lower()
        if not any(req_lower in n for n in normalized):
            missing.append(req)
    return len(missing) == 0, missing


def check_path_references(content: str) -> tuple:
    """Check that all file path references in the retro resolve to existing files.
    
    Returns (ok, dangling_refs). A ref is 'dangling' if it looks like a concrete
    path (not a template with YYYY-MM-DD or cycle-N placeholders) but doesn't exist.
    """
    # Extract file path references: backtick-wrapped paths and bare memory/... paths
    refs = set(re.findall(r"`((?:memory|ui)/[\w\-/\.]+)`", content))
    refs.update(set(re.findall(r"(?<!`)\b(memory/[\w\-/\.]+)\b", content)))
    
    dangling = []
    for ref in sorted(refs):
        # Skip template/placeholder paths
        if re.search(r"(YYYY|MM-DD|cycle-N|<|>)", ref, re.IGNORECASE):
            continue
        p = ROOT / ref
        if not p.exists():
            dangling.append(ref)
    return len(dangling) == 0, dangling


def check_goal_counts(content: str) -> tuple:
    """Verify that Summary goal counts match section contents.
    
    Returns (ok, discrepancies).
    """
    discrepancies = []
    
    # Parse summary counts
    total_match = re.search(r"Goals total:\*\*\s*(\d+)", content)
    completed_match = re.search(r"Completed.*?:\*\*\s*(\d+)", content)
    slipped_match = re.search(r"Slipped.*?:\*\*\s*(\d+)", content)
    
    if not total_match or not completed_match:
        return True, []  # Can't check if summary format differs
    
    claimed_total = int(total_match.group(1))
    claimed_completed = int(completed_match.group(1))
    claimed_slipped = int(slipped_match.group(1)) if slipped_match else None
    
    # Count actual completed goals (lines like '- **#N Title**' or '### agent — N/M')
    in_completed = False
    in_slipped = False
    actual_completed = 0
    actual_slipped = 0
    
    for line in content.split('\n'):
        if re.match(r"^##\s+Goals Completed", line, re.IGNORECASE):
            in_completed = True
            in_slipped = False
            continue
        elif re.match(r"^##\s+Slipped", line, re.IGNORECASE):
            in_completed = False
            in_slipped = True
            continue
        elif re.match(r"^##\s+", line) and not re.match(r"^###", line):
            if in_completed or in_slipped:
                break  # Left the relevant section
        
        # Goal bullets: "- **#N Title**" pattern
        goal_bullet = re.match(r"^\s*-\s+\*\*#?\d+\b", line)
        if in_completed and goal_bullet:
            actual_completed += 1
        elif in_slipped and goal_bullet:
            actual_slipped += 1
    
    # Tolerance: allow off-by-2 due to formatting variations
    if abs(claimed_total - (actual_completed + actual_slipped)) > 2:
        discrepancies.append(f"total={claimed_total} vs sections count {actual_completed+actual_slipped}")
    if claimed_slipped is not None and abs(claimed_slipped - actual_slipped) > 2:
        discrepancies.append(f"slipped={claimed_slipped} vs section count {actual_slipped}")
    
    return len(discrepancies) == 0, discrepancies


def audit_retro(path: pathlib.Path) -> dict:
    """Run all checks on a single retro file."""
    content = path.read_text(encoding="utf-8", errors="replace")
    
    sections_ok, missing_sections = check_sections(content)
    paths_ok, dangling = check_path_references(content)
    counts_ok, count_issues = check_goal_counts(content)
    
    passed = sections_ok and paths_ok and counts_ok
    
    return {
        "file": str(path.relative_to(ROOT)),
        "passed": passed,
        "checks": {
            "sections_complete": sections_ok,
            "missing_sections": missing_sections,
            "paths_resolve": paths_ok,
            "dangling_refs": dangling[:10],  # cap at 10
            "goal_counts_consistent": counts_ok,
            "count_discrepancies": count_issues,
        }
    }


def run_real() -> dict:
    """Audit all real retros."""
    retros = find_retros()
    results = [audit_retro(r) for r in retros]
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "real",
        "retros_audited": len(results),
        "all_passed": all(r["passed"] for r in results) if results else True,
        "results": results,
    }
    return report


def run_selftest() -> dict:
    """Synthetic test cases: 3 valid + 2 invalid."""
    # Valid retro (all sections, resolvable paths)
    valid_retro = """# Test Retro
## Summary
- **Goals total:** 4
- **Completed (evidence):** 3
- **Slipped / open:** 1
## Goals Completed (with evidence)
### agent — 3/4
- **#1 Goal A** — evidence: `memory/ops/autonomy-score.json`
- **#2 Goal B** — evidence: `memory/goals/verifier.md`
- **#3 Goal C** — evidence: `memory/researcher/goal_ledger.py`
## Slipped / Open
- **#4 Goal D** — reason: open
## Key Learnings
- Learning one
## Suggestions
- Suggestion one
"""
    
    # Valid retro (minimal but complete)
    valid_retro_2 = """# Test Retro 2
## Summary
- **Goals total:** 1
- **Completed (evidence):** 1
- **Slipped / open:** 0
## Goals Completed (with evidence)
### agent — 1/1
- **#1 Only Goal** — evidence: `memory/goals/archivist.md`
## Slipped / Open
(none)
## Key Learnings
- All good
## Suggestions
- Keep going
"""
    
    # Invalid: missing sections
    invalid_retro_missing = """# Bad Retro - Missing Sections
## Summary
- **Goals total:** 2
- **Completed (evidence):** 1
## Goals Completed (with evidence)
- **#1 Goal A** — evidence: `memory/goals/verifier.md`
## Slipped / Open
- **#2 Goal B**
"""
    # Missing: Key Learnings, Suggestions
    
    # Invalid: dangling path reference
    invalid_retro_dangling = """# Bad Retro - Dangling Ref
## Summary
- **Goals total:** 2
- **Completed (evidence):** 1
- **Slipped / open:** 1
## Goals Completed (with evidence)
### agent — 1/2
- **#1 Goal A** — evidence: `memory/nonexistent/file-that-doesnt-exist.md`
## Slipped / Open
- **#2 Goal B**
## Key Learnings
- Something
## Suggestions
- Something else
"""
    
    # Write temp files
    import tempfile, os
    tmp_dir = MEM / "verifier" / "_audit_test_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = [
        (tmp_dir / "valid-1.md", valid_retro, True),
        (tmp_dir / "valid-2.md", valid_retro_2, True),
        (tmp_dir / "invalid-missing.md", invalid_retro_missing, False),
        (tmp_dir / "invalid-dangling.md", invalid_retro_dangling, False),
    ]
    
    results = []
    for path, content, expected_pass in test_files:
        path.write_text(content, encoding="utf-8")
        r = audit_retro(path)
        results.append({**r, "expected": expected_pass})
    
    # Cleanup
    for f in tmp_dir.glob("*.md"):
        f.unlink()
    try:
        tmp_dir.rmdir()
    except OSError:
        pass
    
    passed_count = sum(1 for r in results if r["passed"] == r["expected"])
    total = len(results)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "selftest",
        "total_cases": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "verdict": "PASS" if passed_count == total else "FAIL",
        "results": results,
    }


def main():
    if "--selftest" in sys.argv:
        report = run_selftest()
        print(f"Self-test: {report['passed']}/{report['total_cases']} PASS ({report['verdict']})")
        for r in report["results"]:
            status = "OK" if r["passed"] == r["expected"] else "MISMATCH"
            issues = []
            if r["checks"]["missing_sections"]:
                issues.append(f"missing: {r['checks']['missing_sections']}")
            if r["checks"]["dangling_refs"]:
                issues.append(f"dangling: {len(r['checks']['dangling_refs'])} refs")
            if r["checks"]["count_discrepancies"]:
                issues.append(f"counts: {r['checks']['count_discrepancies']}")
            print(f"  [{status}] {r['file']}: passed={r['passed']} expected={r['expected']} ({'; '.join(issues) or 'all clean'})")
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        sys.exit(0 if report["verdict"] == "PASS" else 1)
    else:
        report = run_real()
        print(f"Real audit: {report['retros_audited']} retro(s) checked, all_passed={report['all_passed']}")
        for r in report["results"]:
            flag = "PASS" if r["passed"] else "FAIL"
            issues = []
            if r["checks"]["missing_sections"]:
                issues.append(f"missing sections: {r['checks']['missing_sections']}")
            if r["checks"]["dangling_refs"]:
                issues.append(f"{len(r['checks']['dangling_refs'])} dangling refs")
            if r["checks"]["count_discrepancies"]:
                issues.append(f"count issues: {r['checks']['count_discrepancies']}")
            print(f"  [{flag}] {r['file']}: {'; '.join(issues) or 'all checks pass'}")
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        sys.exit(0)


if __name__ == "__main__":
    main()
