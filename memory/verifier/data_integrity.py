#!/usr/bin/env python3
"""Goal 6: Data Integrity Checks.
Validates cross-file consistency across the project:
  A. agents.json model_ids are non-empty and well-formed
  B. Goal files in memory/goals/ reference valid agent names
  C. INDEX.md pointer targets resolve to real files (root + all sub-indexes)
  D. memory_mirror.py is non-empty (PIN_FILES integrity)

Usage: python memory/verifier/data_integrity.py
Exit: 0 = all checks pass, 1 = issues found (report written).
Report: memory/verifier/data-integrity-report.md
"""
import json, os, re, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # project root
REPORT = HERE / "data-integrity-report.md"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def read_safe(p: Path) -> str:
    """Read file, returning empty string on any error."""
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def check_agents_json():
    """A: model_ids non-empty, no duplicates, valid format."""
    issues = []
    agents_path = ROOT / "agents.json"
    if not agents_path.exists():
        return ["agents.json not found"], []
    try:
        data = json.loads(agents_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"agents.json parse error: {e}"], []

    agents = data.get("agents", [])
    if not isinstance(agents, list):
        return ["agents.json 'agents' is not a list"], []

    seen_ids = set()
    valid_agents = []
    for i, a in enumerate(agents):
        name = a.get("name", f"<unnamed-{i}>")
        mid = a.get("model_id", "")
        if not mid or not mid.strip():
            issues.append(f"agent '{name}': model_id is empty")
        elif not re.match(r'^[a-zA-Z0-9._\-/]+$', mid):
            issues.append(f"agent '{name}': model_id '{mid}' has invalid chars")
        if mid in seen_ids:
            issues.append(f"duplicate model_id '{mid}' (agents: {seen_ids})")
        seen_ids.add(mid)
        valid_agents.append(name)
    return issues, valid_agents


def check_goal_agent_refs(agent_names):
    """B: goal files in memory/goals/ reference valid agent names."""
    issues = []
    goals_dir = ROOT / "memory" / "goals"
    if not goals_dir.exists():
        return ["memory/goals/ directory not found"]

    lower_names = {n.lower() for n in agent_names}
    goal_files = list(goals_dir.glob("*.md"))
    for f in sorted(goal_files):
        stem = f.stem  # e.g. "verifier", "builder-2026-11-20"
        # Extract first token as the agent reference
        first_token = re.split(r'[-_]', stem)[0].lower()
        if first_token in ("index", "all", "cycle", "forecast", "slip",
                           "scheduled", "scheduler", "2026"):
            continue  # non-agent files, skip
        if first_token not in lower_names:
            issues.append(f"{f.name}: references unknown agent '{first_token}'")
    return issues


def check_index_pointers():
    """C: all -> path pointers in INDEX.md files resolve to real files."""
    issues = []
    index_files = list(ROOT.glob("memory/INDEX.md")) + list(ROOT.glob("memory/*/INDEX.md"))
    total_pointers = 0

    for idx in sorted(index_files):
        content = read_safe(idx)
        if not content:
            issues.append(f"{idx.relative_to(ROOT)}: unreadable or empty")
            continue
        # Match -> path: only accept file-path-like tokens (must contain / or end with .ext)
        raw_ptrs = re.findall(r'->\s*([`]?[a-zA-Z0-9_./\\\-]+[`]?)', content)
        for p in raw_ptrs:
            p_clean = p.strip('`').strip()
            # Filter: must look like a file path (has / or ends with common ext)
            if not p_clean or len(p_clean) < 3:
                continue
            has_slash = '/' in p_clean or '\\' in p_clean
            has_ext = bool(re.search(r'\.(md|py|json|js|css|html|txt)$', p_clean))
            if not has_slash and not has_ext:
                continue  # skip prose words like 'pointer', 'goal', etc.
            total_pointers += 1
            # Resolve relative to the index file's parent directory
            base = idx.parent
            candidate = (base / p_clean).resolve()
            if not candidate.exists():
                # Try from project root too
                candidate_root = (ROOT / p_clean).resolve()
                if not candidate_root.exists():
                    issues.append(f"{idx.relative_to(ROOT)}: pointer '{p_clean}' -> file not found")
    return issues, total_pointers


def check_mirror_py():
    """D: memory_mirror.py is non-empty (should contain PIN_FILES logic)."""
    issues = []
    mirror = ROOT / "memory_mirror.py"
    if not mirror.exists():
        issues.append("memory_mirror.py not found")
    else:
        size = mirror.stat().st_size
        if size == 0:
            issues.append("memory_mirror.py is EMPTY (0 bytes) - PIN_FILES logic missing")
        elif size < 100:
            issues.append(f"memory_mirror.py suspiciously small ({size} bytes)")
    return issues


def main():
    results = {}
    all_issues = []

    # A: agents.json
    a_issues, agent_names = check_agents_json()
    results["A_agents_json"] = {"status": "FAIL" if a_issues else "PASS", "issues": a_issues}
    all_issues.extend(a_issues)

    # B: goal agent refs
    b_issues = check_goal_agent_refs(agent_names)
    results["B_goal_agent_refs"] = {"status": "FAIL" if b_issues else "PASS", "issues": b_issues}
    all_issues.extend(b_issues)

    # C: index pointers
    c_issues, total_ptrs = check_index_pointers()
    results["C_index_pointers"] = {
        "status": "FAIL" if c_issues else "PASS",
        "issues": c_issues,
        "total_pointers_checked": total_ptrs
    }
    all_issues.extend(c_issues)

    # D: mirror.py integrity
    d_issues = check_mirror_py()
    results["D_mirror_py"] = {"status": "FAIL" if d_issues else "PASS", "issues": d_issues}
    all_issues.extend(d_issues)

    # Write report
    lines = ["# Data Integrity Report", "", f"Run: {now_iso()}", "",
             f"**Summary: {'ALL PASS' if not all_issues else f'{len(all_issues)} issues found'}**", ""]
    for key, val in results.items():
        icon = "✅" if val["status"] == "PASS" else "❌"
        lines.append(f"## {icon} {key}: {val['status']}")
        extra = f" ({val.get('total_pointers_checked', 0)} pointers checked)" if 'total_pointers_checked' in val else ""
        lines.append(extra)
        for iss in val["issues"]:
            lines.append(f"  - {iss}")
        lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[data_integrity] report -> {REPORT.relative_to(ROOT)}")
    for key, val in results.items():
        status = val["status"]
        n = len(val["issues"])
        print(f"  {key}: {status} ({n} issues)")

    if all_issues:
        print(f"\n[data_integrity] FAIL: {len(all_issues)} total issues")
        sys.exit(1)
    else:
        print("[data_integrity] PASS: 0 issues")
        sys.exit(0)


if __name__ == "__main__":
    main()