#!/usr/bin/env python3
"""pointer_fix_demo.py - demonstrates the tightened pointer regex for index_check.py.

Run: python memory/ops/pointer_fix_demo.py
Shows: old dangling count vs new, and which orphans are auto-generated noise.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEM = ROOT / "memory"

# OLD regex (current in index_check.py)
OLD_RE = re.compile(r"(?:^|\s)->\s*([A-Za-z0-9_./\\-]+)")
MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)\)")

# NEW regex (proposed fix): require / or .ext in target
NEW_RE = re.compile(r"(?:^|\s)->\s*([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_-]+\.[A-Za-z0-9]{1,5})")

# Auto-generated dirs to exclude from orphan count
AUTO_DIRS = {"abstracts", "__pycache__"}
AUTO_EXTS = {".abstract.json", ".pyc"}

def is_plausible_path(tgt: str) -> bool:
    """Returns True if tgt looks like a real file path (not prose)."""
    if "/" in tgt:
        return True
    # has a file extension?  
    parts = tgt.rsplit(".", 1)
    if len(parts) == 2 and 0 < len(parts[1]) <= 5 and parts[1].isalpha():
        return True
    return False

def scan(regex):
    pointers = []
    index_files = [MEM / "INDEX.md"] + sorted(MEM.rglob("INDEX.md"))
    for idx in index_files:
        if not idx.is_file():
            continue
        rel_idx = idx.relative_to(ROOT).as_posix()
        for line in idx.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lstrip().startswith(("#", "Format:")):
                continue
            m = regex.search(line) or MDLINK_RE.search(line)
            if not m:
                continue
            tgt = m.group(1)
            if tgt in ("pointer", "file") or "*" in tgt or "?" in tgt:
                continue
            pointers.append((rel_idx, tgt))
    return pointers

def resolves(tgt: str, idx: Path) -> bool:
    return ((ROOT / tgt).exists()
            or (MEM / tgt).exists()
            or (idx.parent / tgt).resolve().exists())

def main():
    old_ptrs = scan(OLD_RE)
    new_ptrs = scan(NEW_RE)
    
    # Old dangling
    old_dangling = [(s, t) for s, t in old_ptrs if not resolves(t, ROOT / s)]
    # New dangling (only plausible paths that don't resolve)
    new_dangling = [(s, t) for s, t in new_ptrs 
                    if is_plausible_path(t) and not resolves(t, ROOT / s)]
    
    print(f"OLD regex: {len(old_ptrs)} pointer lines, {len(old_dangling)} dangling")
    print(f"NEW regex: {len(new_ptrs)} pointer lines, {len(new_dangling)} dangling")
    print(f"  (old false positives eliminated: {len(old_dangling) - len(new_dangling)})")
    
    if new_dangling:
        print("\nRemaining real dangling pointers:")
        for src, tgt in sorted(set(new_dangling)):
            print(f"  {src} -> {tgt}")
    else:
        print("\nNo real dangling pointers remaining.")
    
    # Orphan analysis
    META = {"INDEX.md", "MEMORY.md", "TODO.md", "VLOG.txt"}
    all_files = {p.relative_to(ROOT).as_posix()
                 for p in MEM.rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts
                 and p.suffix != ".pyc" and p.name not in META}
    
    # Filter out auto-generated noise
    def is_auto_generated(rel: str) -> bool:
        parts = Path(rel).parts
        if any(d in AUTO_DIRS for d in parts):
            return True
        suffix = Path(rel).suffix
        if suffix in {".pyc"}:
            return True
        # .abstract.json files
        if rel.endswith(".abstract.json"):
            return True
        return False
    
    auto_count = sum(1 for f in all_files if is_auto_generated(f))
    real_orphans = {f for f in all_files if not is_auto_generated(f)}
    referenced = set()
    for src, tgt in new_ptrs:
        candidates = {tgt, f"memory/{tgt}"}
        try:
            base = (ROOT / src).parent
            candidates.add((base / tgt).resolve().relative_to(ROOT).as_posix())
        except Exception:
            pass
        referenced.update(candidates)
    
    true_orphans = real_orphans - referenced
    print(f"\nORPHAN analysis:")
    print(f"  Total files: {len(all_files)}")
    print(f"  Auto-generated (excluded): {auto_count}")
    print(f"  Real orphans (not in any INDEX): {len(true_orphans)}")

if __name__ == "__main__":
    main()
