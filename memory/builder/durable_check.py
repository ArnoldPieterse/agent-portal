"""durable_check.py — Durable-copy guarantee enforcement (Scribe goal #6).

Rule: every leaf file under memory/ must be referenced by at least one INDEX.md.
CI-gated: new orphans (files not in baseline AND not indexed) cause hard fail.

Usage:
  python durable_check.py                # check for NEW orphans (not in baseline, not indexed)
  python durable_check.py --all          # report ALL orphans (informational, exit 0)
  python durable_check.py --add-to-baseline <file>  # grandfather a known orphan
  python durable_check.py --ci           # check only git-staged/modified files

Exit codes: 0 = clean, 1 = new orphan(s) found (CI fail), 2 = usage error.
"""
import sys
import re
import json
from pathlib import Path
from datetime import date

ROOT = Path(".")
MEM = ROOT / "memory"
BASELINE_FILE = MEM / "builder" / "durable_check_baseline.jsonl"
TEXT_EXTS = {".md", ".py", ".jsonl", ".json", ".css", ".js", ".html"}
SKIP_NAMES = {"INDEX.md", "MEMORY.md", "TODO.md", "ONBOARDING.md", "blockers.md"}

def collect_index_references() -> set:
    """Return set of paths referenced by any INDEX.md under memory/."""
    refs = set()
    index_files = list(MEM.rglob("INDEX.md"))
    if (MEM / "INDEX.md").is_file():
        index_files.append(MEM / "INDEX.md")
    for idx in set(index_files):
        try:
            content = idx.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Extract full path references
        for m in re.finditer(r'memory/[A-Za-z0-9_\-./]+?\.(?:md|py|jsonl|json|css|js|html)(?!\w)', content):
            refs.add(m.group(0).replace("\\", "/"))
        # Extract basename references (some INDEX files use relative short names)
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("-") and not stripped.startswith("---"):
                # Check for bare filename references (at end of line OR after list dash)
                m = re.search(r'([A-Za-z0-9_\-]+\.(?:md|py|jsonl|json|css|js|html))\s*$', stripped)
                if not m:
                    # Filename mid-line: - filename.ext — description
                    m = re.search(r'^[-*]\s+([A-Za-z0-9_\-]+\.(?:md|py|jsonl|json|css|js|html))\b', stripped)
                if m:
                    refs.add(m.group(1))  # basename only
    return refs

def collect_leaves() -> set:
    """Return all leaf files under memory/ (excluding INDEX files)."""
    leaves = set()
    for p in MEM.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        rel = p.relative_to(ROOT).as_posix()
        # Skip INDEX files themselves
        if p.name.upper().endswith("INDEX.MD"):
            continue
        leaves.add(rel)
    return leaves

def is_referenced(path: str, refs: set) -> bool:
    """Check if a path is referenced (full path or basename match)."""
    if path in refs:
        return True
    basename = path.split("/")[-1]
    if basename in refs:
        return True
    return False

def load_baseline() -> set:
    """Load the grandfathered orphan baseline."""
    if not BASELINE_FILE.is_file():
        return set()
    baseline = set()
    for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            baseline.add(line)
    return baseline

def save_baseline(baseline: set):
    """Persist the baseline (sorted, one per line)."""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = sorted(baseline)
    header = f"# durable_check baseline — {date.today()} — {len(lines)} grandfathered orphans\n"
    BASELINE_FILE.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    args = sys.argv[1:]
    mode = "new"  # default: check for new orphans only
    
    if "--all" in args:
        mode = "all"
    elif "--ci" in args:
        mode = "ci"
    elif "--add-to-baseline" in args:
        idx = args.index("--add-to-baseline")
        if idx + 1 >= len(args):
            print("Error: --add-to-baseline requires a file path argument", file=sys.stderr)
            return 2
        target = args[idx + 1].replace("\\", "/")
        baseline = load_baseline()
        baseline.add(target)
        save_baseline(baseline)
        print(f"Added to baseline: {target} (total: {len(baseline)})")
        return 0
    elif "--init-baseline" in args:
        # Initialize baseline with all current orphans
        refs = collect_index_references()
        leaves = collect_leaves()
        orphans = sorted(f for f in leaves if not is_referenced(f, refs))
        save_baseline(set(orphans))
        print(f"Baseline initialized: {len(orphans)} orphan(s) grandfathered.")
        return 0
    
    refs = collect_index_references()
    leaves = collect_leaves()
    all_orphans = sorted(f for f in leaves if not is_referenced(f, refs))
    
    if mode == "all":
        print(f"[durable] ALL orphans: {len(all_orphans)} / {len(leaves)} leaves")
        for o in all_orphans[:50]:
            print(f"  {o}")
        if len(all_orphans) > 50:
            print(f"  ... and {len(all_orphans) - 50} more")
        return 0
    
    if mode == "ci":
        # CI mode: only check files that would be in a commit (use git if available)
        import subprocess
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True, text=True, timeout=10
            )
            staged = set(l.strip() for l in result.stdout.splitlines() if l.strip())
            # Also check unstaged new files
            result2 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, timeout=10
            )
            untracked = set(l.strip() for l in result2.stdout.splitlines() if l.strip())
            candidates = (staged | untracked) & leaves
        except (FileNotFoundError, subprocess.TimeoutExpired):
            candidates = set(all_orphans)  # fallback: check all
    
    else:  # mode == "new"
        baseline = load_baseline()
        # New orphans = orphans NOT in baseline
        candidates = [o for o in all_orphans if o not in baseline]
    
    if not candidates:
        print(f"[durable] PASS — no new orphan leaves ({len(all_orphans)} grandfathered)")
        return 0
    
    print(f"[durable] FAIL — {len(candidates)} new orphan(s) not referenced by any INDEX.md:")
    for c in sorted(candidates):
        parent_idx = str(Path(c).parent / "INDEX.md")
        print(f"  {c}")
        print(f"    -> add pointer to: {parent_idx}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
