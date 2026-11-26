#!/usr/bin/env python3
"""Post-mirror goal repair: re-apply (verified:) markers stripped by mirror sync.

The mirror sync overwrites memory/goals/*.md from the git-tracked version, which
lacks local evidence markers added by goal_ledger.py --record. This script scans
each main per-agent goal file, finds numbered goal lines that have corresponding
evidence in the lane directory (modified after the goal set date) but are missing
their marker, and re-applies them.

Safety: only touches MAIN_GOAL_FILES (the canonical per-agent .md files), and
only re-applies markers where evidence was created AFTER the goals were set for
the current cycle. This prevents false positives from stale cross-cycle evidence.

Usage: python memory/ops/post_mirror_goal_repair.py [--dry-run]
"""
import pathlib, re, sys, datetime

HERE = pathlib.Path(__file__).resolve().parent.parent.parent  # repo root
GOALS_DIR = HERE / "memory" / "goals"
EVIDENCE_PAT = re.compile(r"\(\s*verified\s*:|(?:\u2014|--)\s*recorded\b")
NUM_LINE = re.compile(r"^\s*(\d+)\.\s+(.+)")

# Only the canonical per-agent goal files (not forecasts, retros, proposals)
MAIN_GOAL_FILES = [
    "archivist.md", "builder.md", "designer.md", "forge.md",
    "mechanic.md", "orchestrator.md", "outlet.md", "pixel.md",
    "researcher.md", "scribe.md", "verifier.md",
]

def find_evidence(agent: str, goal_num: int, min_date: datetime.date):
    """Find evidence file in agent's lane dir, modified after min_date."""
    lane = HERE / "memory" / agent
    if not lane.exists():
        return None
    candidates = []
    for f in lane.iterdir():
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        # Match patterns: goal<N>-*, evidence-goal<N>-*, <agent>-goal<N>-*
        if re.search(rf"(?<!\d)goal{goal_num}[-_.]", name_lower) or \
           re.search(rf"(?<!\d){goal_num}[-_](evidence|verified)", name_lower):
            mtime = datetime.date.fromtimestamp(f.stat().st_mtime)
            if mtime >= min_date:
                candidates.append((mtime, f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return str(candidates[0][1].relative_to(HERE)).replace("\\", "/")

def repair_file(gf: pathlib.Path, dry_run: bool = False) -> int:
    """Repair one goal file. Returns count of markers re-applied."""
    agent = gf.stem
    content = gf.read_text(encoding="utf-8")
    m_set = re.search(r"set\s+(2026-\d{2}-\d{2})", content)
    if not m_set:
        return 0
    set_date = datetime.date.fromisoformat(m_set.group(1))
    lines = content.split("\n")
    repaired = 0
    today = datetime.date.today().isoformat()

    for i, line in enumerate(lines):
        m = NUM_LINE.match(line)
        if not m:
            continue
        goal_num = int(m.group(1))
        if EVIDENCE_PAT.search(line):
            continue
        ev = find_evidence(agent, goal_num, set_date)
        if not ev:
            continue
        marker = f" (verified: {today} - {ev})"
        lines[i] = line.rstrip() + marker
        repaired += 1

    if repaired > 0 and not dry_run:
        gf.write_text("\n".join(lines), encoding="utf-8")
    return repaired

def main():
    dry_run = "--dry-run" in sys.argv
    total = 0
    for name in MAIN_GOAL_FILES:
        gf = GOALS_DIR / name
        if not gf.exists():
            continue
        n = repair_file(gf, dry_run)
        if n > 0:
            print(f"  {'[DRY] ' if dry_run else ''}{name}: {n} marker(s) re-applied")
            total += n
    if total == 0:
        print("  No repairs needed.")
    else:
        print(f"  Total: {total} marker(s) {'would be' if dry_run else 'repaired'}.")

if __name__ == "__main__":
    main()
