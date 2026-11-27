#!/usr/bin/env python3
"""tree_reclaim.py - safe, dry-run-by-default reclamation for the memory tree.

Companion to archivist/size_guard.py (WARN>200MB / FAIL>300MB, recalibrated 2026-11-23).
prune_memory_tree.py covers age-based rules; THIS handles the consolidation strategies
that broke the guard's convergence after 2026-11-25: stale merge-queue snapshots,
regenerable browser-profile artifact dirs, and redundant same-scope fleet backups.

Strategies (all reversible-in-principle, all verified before delete):
  1. merge-queue : keep newest KEEP_N snapshots per base file, drop older .<hash> copies
  2. profiles    : remove Playwright/Edge user-data-dir artifacts (.edge-*, _edge_profile)
  3. backups     : keep only the NEWEST fleet-backup-*.tar.gz (+ sidecar), drop older same-scope

Usage:
  python memory/ops/tree_reclaim.py            # dry-run (default, nothing deleted)
  python memory/ops/tree_reclaim.py --apply    # execute deletions
  python memory/ops/tree_reclaim.py --keep-n 10
Exit 0 = projected under HARD line after reclaim; 1 = still over.
"""
import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # project root (parent of memory/)
WARN_BYTES = 200 * 1024 * 1024
HARD_BYTES = 300 * 1024 * 1024
KEEP_N_DEFAULT = 5


def tree_size(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # skip VCS + bytecode noise (matches size_guard intent)
        dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__')]
        for f in filenames:
            fp = Path(dirpath) / f
            if fp.is_file():
                total += fp.stat().st_size
    return total


def base_of(name: str):
    """Split 'agent_portal.py.e5e75fd04d' -> ('agent_portal.py', 'e5e75fd04d'). None if not a snapshot."""
    stem, dot, tail = name.rpartition('.')
    if dot and len(tail) == 10 and all(c in '0123456789abcdef' for c in tail):
        return stem, tail
    return None


def plan_merge_queue(root: Path, keep_n: int):
    mq = root / 'memory' / 'ops' / 'merge-queue'
    to_del = []
    if not mq.exists():
        return to_del
    groups = defaultdict(list)
    for f in mq.iterdir():
        if not f.is_file():
            continue
        b = base_of(f.name)
        if b:
            groups[b[0]].append((f.stat().st_mtime, f))
    for base, items in groups.items():
        items.sort(reverse=True)  # newest first
        for _, f in items[keep_n:]:
            to_del.append(f)
    return to_del


def plan_profiles(root: Path):
    to_del = []   # list of top-level dirs to remove wholesale
    mem = root / 'memory'
    if not mem.exists():
        return to_del
    for d in mem.rglob('*'):
        if not d.is_dir():
            continue
        name = d.name
        if name.startswith('.edge') or name == '_edge_profile':
            # only take the profile ROOT (the one that directly contains 'Default'), avoid double-counting children
            if (d / 'Default').is_dir() or any(c.name.startswith('Crashpad') for c in d.iterdir()):
                to_del.append(d)
    # de-dup: drop any dir that is inside another selected dir
    to_del.sort(key=lambda p: len(p.parts))
    kept = []
    for d in to_del:
        if not any(d == k or k in d.parents for k in kept):
            kept.append(d)
    return kept


def plan_backups(root: Path):
    bk = root / 'memory' / 'mechanic' / 'backups'
    to_del = []
    if not bk.exists():
        return to_del
    tgs = [f for f in bk.iterdir() if f.is_file() and f.name.startswith('fleet-backup-') and f.name.endswith('.tar.gz')]
    if len(tgs) <= 1:
        return to_del
    newest = max(tgs, key=lambda f: f.stat().st_mtime)
    for f in tgs:
        if f != newest:
            to_del.append(f)
            side = f.with_suffix('.tar.json')
            if side.exists():
                to_del.append(side)
    return to_del


def main():
    ap = argparse.ArgumentParser(description='Safe memory-tree reclamation (dry-run default)')
    ap.add_argument('--apply', action='store_true', help='Execute deletions (default: dry-run)')
    ap.add_argument('--keep-n', type=int, default=KEEP_N_DEFAULT, help='Merge-queue snapshots to keep per base file')
    args = ap.parse_args()

    # size_guard.py measures memory/ only (ROOT here is project root for path building)
    before = tree_size(ROOT / 'memory')
    mq_del = plan_merge_queue(ROOT, args.keep_n)
    prof_del = plan_profiles(ROOT)
    bk_del = plan_backups(ROOT)

    def sz(paths):
        return sum(p.stat().st_size for p in paths if p.is_file())

    def dirsz(d):
        return sum(f.stat().st_size for f in d.rglob('*') if f.is_file())

    mq_mb = sz(mq_del) / 1048576.0
    prof_mb = sum(dirsz(d) for d in prof_del) / 1048576.0
    bk_mb = sz(bk_del) / 1048576.0
    total_mb = mq_mb + prof_mb + bk_mb

    act = 'DELETE' if args.apply else 'WOULD DELETE'
    print(f"Current tree: {before/1048576.0:.2f} MB  (WARN>{WARN_BYTES/1048576:.0f}MB FAIL>{HARD_BYTES/1048576:.0f}MB)")
    print(f"\n[merge-queue] {len(mq_del)} stale snapshots, {mq_mb:.2f} MB  (keep newest {args.keep_n}/base)")
    for f in sorted(mq_del, key=lambda p: -p.stat().st_size)[:8]:
        print(f"   {act} {f.relative_to(ROOT)}")
    if len(mq_del) > 8:
        print(f"   ... +{len(mq_del)-8} more")
    print(f"\n[browser-profiles] {len(prof_del)} dirs, {prof_mb:.2f} MB  (regenerable Playwright/Edge user-data)")
    for d in prof_del:
        print(f"   {act} {d.relative_to(ROOT)}/")
    print(f"\n[fleet-backups] {len([p for p in bk_del if p.suffix=='.tar.gz'])} older tarballs, {bk_mb:.2f} MB  (keep newest same-scope)")
    for f in sorted(bk_del, key=lambda p: -p.stat().st_size):
        print(f"   {act} {f.relative_to(ROOT)}")

    projected = before - total_mb * 1048576.0
    print(f"\nReclaimable: {total_mb:.2f} MB -> projected {projected/1048576.0:.2f} MB -> "
          f"{'PASS' if projected < HARD_BYTES else 'STILL OVER'}")

    if args.apply:
        deleted = 0
        for f in mq_del + bk_del:
            try:
                f.unlink(); deleted += 1
            except OSError as e:
                print(f"   FAILED {f}: {e}")
        import shutil
        for d in prof_del:
            try:
                shutil.rmtree(d); deleted += 1
            except OSError as e:
                print(f"   FAILED {d}: {e}")
        after = tree_size(ROOT / 'memory')
        print(f"\nApplied. Deleted {deleted} items. Tree now: {after/1048576.0:.2f} MB "
              f"(reclaimed {(before-after)/1048576.0:.2f} MB) -> "
              f"{'PASS' if after < HARD_BYTES else 'STILL OVER'}")

    sys.exit(0 if projected < HARD_BYTES else 1)


if __name__ == '__main__':
    main()
