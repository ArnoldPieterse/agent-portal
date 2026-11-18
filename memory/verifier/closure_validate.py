"""Goal Closure Validator - validates that a goal meets all closure criteria before it can be marked done.

Usage: python memory/verifier/closure_validate.py <agent> <goal#> [--verbose]

Checks:
  (a) Evidence file exists
  (b) Evidence file is non-empty
  (c) verified: marker present on the goal line
  (d) No open sub-tasks (no unchecked checkboxes below the goal)

Exit codes:
  0 = all checks pass (goal is validly closed)
  1 = one or more checks fail
  2 = usage error / goal not found
"""
import os, re, sys, argparse
from typing import List, Tuple, Optional

GOALS_DIR = "memory/goals"
VERIFIED_RE = re.compile(r'\(verified:\s*|Verified:\s*')
EVIDENCE_RE = re.compile(r'(?:evidence at|Evidence:|evidence:|pointer:)\s+(\S[\w/._-]+)')
PATH_RE = re.compile(r'((?:memory|ui|agents\.json|TODO\.md|MEMORY\.md)[\w/._-]*\.\w+)')
UNCHECKED_BOX_RE = re.compile(r'^\s*[-*]\s+\[ \]')


def find_goal_file(agent: str) -> Optional[str]:
    """Find the goal file for an agent (active or archived)."""
    # Active file first
    active = os.path.join(GOALS_DIR, f"{agent}.md")
    if os.path.isfile(active):
        return active
    # Check archive subdirs
    archive_dir = os.path.join(GOALS_DIR, "archive")
    if os.path.isdir(archive_dir):
        for root, dirs, files in os.walk(archive_dir):
            for f in files:
                if f == f"{agent}.md" or (f.startswith(agent) and f.endswith('.md')):
                    return os.path.join(root, f)
    # Check cycle subdirs
    for root, dirs, files in os.walk(GOALS_DIR):
        for f in files:
            if f == f"{agent}.md":
                p = os.path.join(root, f)
                if p != active and os.path.isfile(p):
                    return p
    return None


def extract_goal_line(text: str, goal_num: int) -> Tuple[Optional[int], Optional[str]]:
    """Find the line for a given goal number. Returns (line_number, line_text)."""
    lines = text.split('\n')
    # Match patterns like "1. **", "## 1.", "- 1." etc.
    pattern = re.compile(rf'^\s*{goal_num}\.\s+')
    for i, line in enumerate(lines):
        if pattern.match(line):
            return (i + 1, line)
    return (None, None)


def extract_subtasks(text: str, goal_line_num: int, goal_num: int) -> List[Tuple[int, str]]:
    """Find unchecked sub-tasks between this goal and the next numbered goal."""
    lines = text.split('\n')
    # Find where this goal ends (next numbered item at same or higher number)
    end_pattern = re.compile(rf'^\s*({goal_num + 1}|\d+\.\s*\*\*)')
    subtasks = []
    for i in range(goal_line_num, len(lines)):
        line = lines[i]
        # Stop at next goal number
        if i > goal_line_num - 1 and re.match(rf'^\s*\d+\.\s', line):
            break
        if UNCHECKED_BOX_RE.match(line):
            subtasks.append((i + 1, line.strip()))
    return subtasks


def validate(agent: str, goal_num: int, verbose: bool = False) -> int:
    goal_file = find_goal_file(agent)
    if not goal_file:
        print(f"FAIL: No goal file found for agent '{agent}'")
        return 2

    text = open(goal_file, 'r', encoding='utf-8', errors='replace').read()
    line_num, goal_line = extract_goal_line(text, goal_num)
    if not goal_line:
        print(f"FAIL: Goal #{goal_num} not found in {goal_file}")
        return 2

    if verbose:
        print(f"File: {goal_file}")
        print(f"Line {line_num}: {goal_line[:100]}")

    results = []
    all_pass = True

    # (c) Check for verified marker
    has_verified = bool(VERIFIED_RE.search(goal_line))
    results.append(("verified: marker present", has_verified, "" if has_verified else "No 'verified:' or '(verified:' found on goal line"))

    # (a) & (b) Check evidence file exists and is non-empty
    # Extract text from within the (verified:...) marker only, not the whole line.
    # Use last ')' to handle nested parens like "(port blocked)" inside the marker.
    verified_section = ''
    vstart = goal_line.find('(verified:')
    if vstart == -1:
        vstart = goal_line.find('Verified:')
    if vstart != -1:
        # Skip past '(verified:' or 'Verified:' to get the content
        content_start = goal_line.index(':', vstart) + 1
        tail = goal_line[content_start:]
        last_paren = tail.rfind(')')
        verified_section = tail[:last_paren] if last_paren != -1 else tail
    else:
        verified_section = ''

    paths = set()
    for m in EVIDENCE_RE.finditer(verified_section):
        p = m.group(1).rstrip('.,;')
        if not p.startswith('http'):
            paths.add(p)
    for m in PATH_RE.finditer(verified_section):
        paths.add(m.group(1))

    if not paths:
        results.append(("evidence file exists", False, "No evidence path found in goal line"))
        all_pass = False
    else:
        for ep in sorted(paths):
            full_ep = ep.replace('/', os.sep)
            if not os.path.isfile(full_ep):
                results.append((f"evidence '{ep}' exists", False, f"File not found: {full_ep}"))
                all_pass = False
            else:
                size = os.path.getsize(full_ep)
                if size == 0:
                    results.append((f"evidence '{ep}' non-empty", False, "File is empty (0 bytes)"))
                    all_pass = False
                else:
                    results.append((f"evidence '{ep}' exists + non-empty", True, f"{size} bytes"))

    # (d) Check for open sub-tasks
    subtasks = extract_subtasks(text, line_num, goal_num)
    if subtasks:
        results.append(("no open sub-tasks", False, f"{len(subtasks)} unchecked task(s) found"))
        all_pass = False
    else:
        results.append(("no open sub-tasks", True, ""))

    # Report
    print(f"\nCLOSURE VALIDATION: {agent} goal #{goal_num}")
    print(f"{'='*50}")
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        msg = f"  [{status}] {name}"
        if detail and not passed:
            msg += f" - {detail}"
        print(msg)

    # Final verdict
    print(f"\n  RESULT: {'VALID (all checks pass)' if all_pass else 'INVALID (closure blocked)'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate goal closure criteria")
    parser.add_argument("agent", help="Agent name (e.g. verifier, builder)")
    parser.add_argument("goal", type=int, help="Goal number (e.g. 1)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    sys.exit(validate(args.agent, args.goal, args.verbose))
