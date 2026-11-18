#!/usr/bin/env python3
"""Evidence Freshness Audit - scans goal files for (verified:) markers and checks
evidence file existence + staleness.

Usage: python memory/verifier/freshness_audit.py [--stale-days 7] [--verbose]

Exit codes:
  0 = all evidence fresh and present
  1 = stale or missing evidence found (details printed)
  2 = no goal files found
"""
import os, re, sys, time, argparse
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

GOALS_DIR = "memory/goals"
EVIDENCE_RE = re.compile(r'(?:evidence at|Evidence:|evidence:|pointer:)\s+(\S[\w/._-]+)')
VERIFIED_RE = re.compile(r'\(verified:\s*(.*?)\)', re.DOTALL)
DATE_RE = re.compile(r'(20\d{2}-\d{2}-\d{2})')

# Also catch inline paths that look like memory/... or agents.json etc.
PATH_RE = re.compile(r'((?:memory|ui|agents\.json|TODO\.md|MEMORY\.md)[\w/._-]*\.\w+)')


def extract_evidence_paths(verified_text: str) -> List[str]:
    """Extract evidence file paths from a verified marker's text."""
    paths = set()
    # Explicit "evidence at X" or "Evidence: X" patterns
    for m in EVIDENCE_RE.finditer(verified_text):
        p = m.group(1).rstrip('.,;')
        if not p.startswith('http'):
            paths.add(p)
    # Fallback: any path-looking token that starts with memory/ or ui/
    for m in PATH_RE.finditer(verified_text):
        paths.add(m.group(1))
    return sorted(paths)


def get_verified_date(verified_text: str) -> Optional[datetime]:
    """Extract the date from a verified marker."""
    m = DATE_RE.search(verified_text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return None


def audit(stale_days: int = 7, verbose: bool = False) -> int:
    goals_dir = GOALS_DIR
    if not os.path.isdir(goals_dir):
        print(f"FATAL: {goals_dir} not found")
        return 2

    goal_files = []
    for root, dirs, files in os.walk(goals_dir):
        for f in files:
            if f.endswith('.md'):
                goal_files.append(os.path.join(root, f))

    if not goal_files:
        print(f"FATAL: no .md files found in {goals_dir}")
        return 2

    now = datetime.now()
    stale_cutoff = now - timedelta(days=stale_days)

    total_verified = 0
    missing_evidence = []   # (file, goal_line, evidence_path)
    stale_evidence = []     # (file, goal_line, evidence_path, age_days)
    no_path_refs = []       # (file, goal_line) - verified but no path found

    for gf in sorted(goal_files):
        try:
            text = open(gf, 'r', encoding='utf-8', errors='replace').read()
        except Exception as e:
            if verbose:
                print(f"  [WARN] cannot read {gf}: {e}")
            continue

        lines = text.split('\n')
        for line_no, line in enumerate(lines, 1):
            for vm in VERIFIED_RE.finditer(line):
                total_verified += 1
                vtext = vm.group(1)
                paths = extract_evidence_paths(vtext)

                if not paths:
                    no_path_refs.append((gf, line_no, vtext[:80]))
                    continue

                for ep in paths:
                    full_ep = ep.replace('/', os.sep)
                    exists = os.path.isfile(full_ep)
                    if not exists:
                        missing_evidence.append((gf, line_no, ep))
                    else:
                        mtime = datetime.fromtimestamp(os.path.getmtime(full_ep))
                        age_days = (now - mtime).days
                        size = os.path.getsize(full_ep)
                        if size == 0:
                            missing_evidence.append((gf, line_no, ep + " [EMPTY]"))
                        elif mtime < stale_cutoff:
                            stale_evidence.append((gf, line_no, ep, age_days))

    # Report
    print(f"\n{'='*60}")
    print(f"EVIDENCE FRESHNESS AUDIT")
    print(f"  Scan date: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Stale threshold: {stale_days} days")
    print(f"  Goal files scanned: {len(goal_files)}")
    print(f"{'='*60}")

    print(f"\n  Total (verified:) markers found: {total_verified}")

    if missing_evidence:
        print(f"\n  ✗ MISSING/EMPTY EVIDENCE ({len(missing_evidence)}):")
        for gf, ln, ep in missing_evidence[:20]:
            rel = os.path.relpath(gf)
            print(f"    {rel}:{ln} -> {ep}")
        if len(missing_evidence) > 20:
            print(f"    ... and {len(missing_evidence)-20} more")

    if stale_evidence:
        print(f"\n  ⚠ STALE EVIDENCE ({len(stale_evidence)}):")
        for gf, ln, ep, age in stale_evidence[:20]:
            rel = os.path.relpath(gf)
            print(f"    {rel}:{ln} -> {ep} ({age}d old)")
        if len(stale_evidence) > 20:
            print(f"    ... and {len(stale_evidence)-20} more")

    if no_path_refs:
        print(f"\n  ℹ NO EVIDENCE PATH REF ({len(no_path_refs)}): (verified markers without file reference)")
        for gf, ln, snippet in no_path_refs[:10]:
            rel = os.path.relpath(gf)
            print(f"    {rel}:{ln} -> {snippet}...")

    passed = len(missing_evidence) == 0 and len(stale_evidence) == 0
    status = "PASS" if passed else "FAIL"
    print(f"\n{'='*60}")
    print(f"  RESULT: {status}")
    print(f"  Missing/empty: {len(missing_evidence)} | Stale: {len(stale_evidence)} | No path ref: {len(no_path_refs)}")
    print(f"{'='*60}\n")

    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evidence Freshness Audit")
    parser.add_argument("--stale-days", type=int, default=7, help="Days before evidence is considered stale (default 7)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    sys.exit(audit(args.stale_days, args.verbose))