#!/usr/bin/env python3
"""archivist/index_check.py - repeatable index-integrity sweep (Archivist goal 2).

Walks memory/, parses every INDEX.md pointer line ("-> <path>", resolved
relative to repo root), and reports:
  DANGLING : pointer targets that do not exist on disk      -> hard fail
  ORPHANS  : files under memory/ referenced by no INDEX.md  -> soft fail
  STALE    : "Last updated:" date older than today          -> warning only

Exit codes: 0 = clean, 1 = dangling pointers found, 2 = orphans only.
Run from repo root:  python memory/archivist/index_check.py
"""
import re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEM = ROOT / "memory"
ARROW_RE = re.compile(r"(?:^|\s)->\s*([A-Za-z0-9_./\\-]+)")
MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)\)")
DATE_RE = re.compile(r"Last updated:\s*(\d{4}-\d{2}-\d{2})")

def main() -> int:
    today = date.today()
    index_files = [MEM / "INDEX.md"] + sorted(MEM.rglob("INDEX.md"))
    index_files = [p for p in dict.fromkeys(index_files) if p.is_file()]

    pointers, stale = [], []
    for idx in index_files:
        rel_idx = idx.relative_to(ROOT).as_posix()
        for line in idx.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lstrip().startswith(("#", "Format:")):
                continue  # header / format-description lines are not pointers
            m = ARROW_RE.search(line) or MDLINK_RE.search(line)
            if m:
                tgt = m.group(1)
                if tgt in ("pointer", "file"):  # convention words, not paths
                    continue
                pointers.append((rel_idx, tgt))
        d = DATE_RE.search(idx.read_text(encoding="utf-8", errors="replace"))
        if d:
            y, mo, da = map(int, d.group(1).split("-"))
            if date(y, mo, da) < today:
                stale.append((rel_idx, d.group(1)))

    all_files = {p.relative_to(ROOT).as_posix()
                 for p in MEM.rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts}
    referenced = set()
    for src, tgt in pointers:
        candidates = {tgt, f"memory/{tgt}"}
        try:
            base = (ROOT / src).parent
            candidates.add((base / tgt).resolve().relative_to(ROOT).as_posix())
        except Exception:
            pass
        referenced.update(candidates)

    def resolves(tgt: str, idx: Path) -> bool:
        # try root-relative, memory/-relative (sub-index convention),
        # and the index file's own directory (for ../ style links)
        return ((ROOT / tgt).exists()
                or (MEM / tgt).exists()
                or (idx.parent / tgt).resolve().exists())

    dangling = sorted({(src, tgt) for src, tgt in pointers
                       if not resolves(tgt, ROOT / src)})
    orphans = sorted(all_files - referenced - {"memory/INDEX.md"})

    print(f"index_check  root={ROOT.name}  today={today}")
    print(f"indexes scanned: {len(index_files)}   pointer lines: {len(pointers)}   files under memory/: {len(all_files)}")
    print()
    print(f"DANGLING pointers ({len(dangling)}):")
    for src, tgt in dangling:
        print(f"  {src} -> {tgt}")
    print(f"ORPHANS - not referenced by any INDEX.md ({len(orphans)}):")
    for f in orphans:
        print(f"  {f}")
    print(f"STALE 'Last updated' ({len(stale)}):")
    for src, d in stale:
        print(f"  {src}: {d}")

    if dangling:
        return 1
    if orphans:
        return 2
    print("CLEAN")
    return 0

if __name__ == "__main__":
    sys.exit(main())
