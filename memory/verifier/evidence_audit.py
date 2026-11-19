#!/usr/bin/env python3
"""Evidence Freshness Audit (Goal 2 - cycle-7).

Scans all active goal files in memory/goals/ for (verified:) markers,
flags any older than the stale threshold (default: 14 days) as STALE,
and writes an actionable markdown report to memory/verifier/stale-evidence-YYYY-MM-DD.md.

Usage:
    python memory/verifier/evidence_audit.py [--stale-days 14] [--verbose]

Exit codes:
    0 = all verified claims fresh (within threshold) or no claims found
    1 = one or more stale claims detected (report written)
    2 = error (no goal files found, etc.)
"""
import os, re, sys, argparse
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict

GOALS_DIR = "memory/goals"
REPORT_DIR = "memory/verifier"
DEFAULT_STALE_DAYS = 14

VERIFIED_RE = re.compile(r'\(verified:\s*(.*?)\)', re.DOTALL)
DATE_RE = re.compile(r'(20\d{2}-\d{2}-\d{2})')
PATH_RE = re.compile(r'(?<![\w.])((?:memory|ui)/[\w/._-]*\.\w+|(?:agents\.json|TODO\.md|MEMORY\.md))')
SCRIPT_RE = re.compile(r'(python\s+\S+\.py\S*|\S+\.py\s+[\w\-]*)')

def extract_paths(text: str) -> List[str]:
    paths = set()
    for m in PATH_RE.finditer(text):
        paths.add(m.group(1))
    return sorted(paths)

def get_date(text: str) -> Optional[datetime]:
    m = DATE_RE.search(text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return None

def suggest_command(vtext: str, goal_line: str) -> str:
    """Derive a re-verification command from the verified text and goal line."""
    # Look for python script references
    scripts = SCRIPT_RE.findall(vtext) + SCRIPT_RE.findall(goal_line)
    if scripts:
        return f"python {scripts[0].strip()}"
    # Look for endpoint references
    ep_match = re.search(r'(/api/[\w/]+)', vtext + goal_line)
    if ep_match:
        return f"curl -s http://localhost:8099{ep_match.group(1)} | python -m json.tool"
    # Fallback: re-run the goal file's associated test if findable
    path_refs = extract_paths(vtext + goal_line)
    for p in path_refs:
        if p.endswith('.py'):
            return f"python {p}"
    return "# re-verify manually (no auto command derivable)"

def audit(stale_days: int = DEFAULT_STALE_DAYS, verbose: bool = False) -> int:
    now = datetime.now()
    stale_cutoff = now - timedelta(days=stale_days)
    today = now.strftime("%Y-%m-%d")

    if not os.path.isdir(GOALS_DIR):
        print(f"FATAL: {GOALS_DIR} not found", file=sys.stderr)
        return 2

    goal_files = []
    for root, dirs, files in os.walk(GOALS_DIR):
        for f in files:
            if f.endswith('.md'):
                goal_files.append(os.path.join(root, f))

    if not goal_files:
        print(f"FATAL: no .md files found in {GOALS_DIR}", file=sys.stderr)
        return 2

    total = 0
    stale: List[Dict] = []
    fresh: List[Dict] = []

    for gf in sorted(goal_files):
        try:
            text = open(gf, 'r', encoding='utf-8', errors='replace').read()
        except Exception as e:
            if verbose:
                print(f"  [WARN] cannot read {gf}: {e}", file=sys.stderr)
            continue

        for line_no, line in enumerate(text.split('\n'), 1):
            for vm in VERIFIED_RE.finditer(line):
                total += 1
                vtext = vm.group(1).strip()
                vdate = get_date(vtext)
                age_days = (now - vdate).days if vdate else None

                paths = extract_paths(vtext)
                missing = [p for p in paths if not os.path.isfile(p.replace('/', os.sep))]

                entry = {
                    "file": gf,
                    "line": line_no,
                    "vtext": vtext[:120],
                    "date": str(vdate.date()) if vdate else "unknown",
                    "age_days": age_days,
                    "paths": paths,
                    "missing": missing,
                }

                is_stale = (age_days is not None and age_days > stale_days) or bool(missing)
                if is_stale:
                    entry["reason"] = []
                    if age_days is not None and age_days > stale_days:
                        entry["reason"].append(f"{age_days}d old (> {stale_days}d)")
                    if missing:
                        entry["reason"].append(f"missing evidence: {', '.join(missing)}")
                    entry["reverify_cmd"] = suggest_command(vtext, line)
                    stale.append(entry)
                else:
                    fresh.append(entry)

    # Write report
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"stale-evidence-{today}.md")
    lines = [
        f"# Evidence Freshness Audit — {today}",
        "",
        f"**Threshold:** {stale_days} days  ",
        f"**Goal files scanned:** {len(goal_files)}  ",
        f"**Total (verified:) markers:** {total}  ",
        f"**Stale/missing:** {len(stale)}  ",
        f"**Fresh:** {len(fresh)}",
        "",
    ]

    if stale:
        lines.append("## STALE / MISSING Claims\n")
        for i, e in enumerate(stale, 1):
            rel = os.path.relpath(e["file"])
            lines.append(f"### {i}. `{rel}:{e['line']}`")
            lines.append(f"- **Date:** {e['date']} ({e['age_days']}d old)" if e['age_days'] else f"- **Date:** {e['date']}")
            lines.append(f"- **Reason:** {'; '.join(e['reason'])}")
            if e["paths"]:
                lines.append(f"- **Evidence paths:** {', '.join('`' + p + '`' for p in e['paths'])}")
            lines.append(f"- **Re-verify:** `{e['reverify_cmd']}`")
            lines.append("")
    else:
        lines.append("## Result\n")
        lines.append("All verified claims are fresh. No action needed.\n")

    report = "\n".join(lines)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    # Console summary
    print(f"\n{'='*60}")
    print(f"EVIDENCE FRESHNESS AUDIT  {today}")
    print(f"  Threshold: {stale_days}d | Files scanned: {len(goal_files)}")
    print(f"  Total verified markers: {total}")
    print(f"  Fresh: {len(fresh)} | Stale/missing: {len(stale)}")
    print(f"  Report: {report_path}")
    if stale:
        for e in stale[:10]:
            rel = os.path.relpath(e["file"])
            reason = '; '.join(e["reason"])
            print(f"    STALE: {rel}:{e['line']} [{reason}]")
    print(f"{'='*60}\n")

    return 1 if stale else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evidence Freshness Audit (Goal 2)")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    sys.exit(audit(args.stale_days, args.verbose))
