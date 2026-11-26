#!/usr/bin/env python3
"""Prune the memory tree to stay under size limits.
Dry-run by default; --apply actually deletes.
Exit 0 = under limit after prune (or would be); 1 = still over.
"""
import argparse, os, sys, time, glob as globmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LIMIT_BYTES = 5 * 1024 * 1024  # 5 MB hard limit (size_guard target)
PRACTICAL_LIMIT = 50 * 1024 * 1024  # practical target with headroom

PRUNE_RULES = [
    # (path_glob_relative_to_ROOT, max_age_days, description)
    ("memory/mechanic/backups/fleet-backup-*.tar.gz", 5, "Fleet backups >5d"),
    ("memory/archivist/dedup-report*.json", 5, "Dedup reports >5d"),
    ("_edgeud/Crashpad/reports/*", 1, "Edge crashpad >24h"),
    ("edgeprofile/Crashpad/reports/*", 1, "Edge profile crashpad >24h"),
    ("Packages/*/AC/Temp/*/Crashpad/reports/*", 1, "Sandbox crashpad >24h"),
]


def tree_size(root: Path) -> int:
    total = 0
    for dirpath, _, filenames in os.walk(root):
        if '.git' in dirpath or '__pycache__' in dirpath:
            continue
        for f in filenames:
            try:
                total += (Path(dirpath) / f).stat().st_size
            except OSError:
                pass
    return total


def find_prunable(root: Path):
    """Return list of (path, size, age_days, rule_desc) matching prune rules."""
    prunable = []
    now = time.time()
    for pattern, max_age, desc in PRUNE_RULES:
        full_pattern = str(root / pattern)
        for fp in globmod.glob(full_pattern):
            p = Path(fp)
            if not p.exists():
                continue
            try:
                st = p.stat()
                age_days = (now - st.st_mtime) / 86400
                if age_days > max_age:
                    prunable.append((p, st.st_size, age_days, desc))
            except OSError:
                pass
    return prunable


def main():
    ap = argparse.ArgumentParser(description="Prune memory tree to size limit")
    ap.add_argument('--apply', action='store_true', help='Actually delete (default: dry-run)')
    ap.add_argument('--limit-mb', type=float, default=50, help='Target total size in MB')
    args = ap.parse_args()

    limit = int(args.limit_mb * 1024 * 1024)
    current = tree_size(ROOT)
    print(f"Current tree size: {current/1024/1024:.1f} MB (target: {args.limit_mb} MB)")

    prunable = find_prunable(ROOT)
    total_reclaimable = sum(sz for _, sz, _, _ in prunable)
    print(f"Prunable items: {len(prunable)} files, {total_reclaimable/1024/1024:.1f} MB reclaimable")

    if prunable:
        print("\nItems to prune (top 20 by size):")
        for p, sz, age, desc in sorted(prunable, key=lambda x: -x[1])[:20]:
            action = "DELETE" if args.apply else "WOULD DELETE"
            try:
                rel = p.relative_to(ROOT)
            except ValueError:
                rel = p
            print(f"  {action} [{sz/1024:.0f} KB, {age:.0f}d old] {rel} ({desc})")
        if len(prunable) > 20:
            print(f"  ... and {len(prunable)-20} more")

    projected = current - total_reclaimable
    status = "PASS" if projected < limit else "STILL OVER"
    print(f"\nProjected size after prune: {projected/1024/1024:.1f} MB -> {status}")

    if args.apply and prunable:
        deleted = 0
        for p, sz, age, desc in prunable:
            try:
                p.unlink()
                deleted += 1
            except OSError as e:
                print(f"  FAILED: {p} ({e})")
        print(f"\nDeleted {deleted}/{len(prunable)} files.")

    sys.exit(0 if projected < limit else 1)


if __name__ == '__main__':
    main()
