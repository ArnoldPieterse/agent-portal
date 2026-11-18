#!/usr/bin/env python3
"""Memory Hygiene Report: audit memory/ directory.

Metrics:
  - Total file count + total size
  - Files >5KB (should be split per modularity rule)
  - Orphaned files (not referenced by any INDEX.md in the same tree)
  - Stale files (>30 days since last edit)

Usage: python memory/scribe/hygiene_report.py [--write]
With --write, outputs to memory/scribe/hygiene-report-YYYY-MM-DD.md
Exit 0 = report generated; exit 1 = error.
"""
import os, re, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

MEMORY_DIR = Path(__file__).resolve().parent.parent
MAX_SIZE_KB = 5
STALE_DAYS = 30

def get_all_files(directory: Path) -> list:
    """Get all .md and .py files in memory/ recursively."""
    files = []
    for f in directory.rglob('*'):
        if f.is_file() and f.suffix in ('.md', '.py', '.json'):
            files.append(f)
    return sorted(files)

def find_index_refs(directory: Path) -> set:
    """Collect all file references from INDEX.md files."""
    refs = set()
    for idx in directory.rglob('INDEX.md'):
        try:
            text = idx.read_text(encoding='utf-8', errors='replace')
            # Match relative paths like memory/..., or bare filenames
            for m in re.finditer(r'(?:->\s*|`)([\w./-]+\.(?:md|py|json))', text):
                refs.add(m.group(1).strip())
        except Exception:
            pass
    return refs

def is_referenced(filepath: Path, index_refs: set, memory_dir: Path) -> bool:
    """Check if a file is referenced by any INDEX.md."""
    rel = filepath.relative_to(memory_dir.parent).as_posix()
    # Also check just the filename
    name = filepath.name
    for ref in index_refs:
        if ref == rel or ref.endswith(name) or name in ref:
            return True
    # Check if it's an INDEX.md itself (self-referential)
    if filepath.name == 'INDEX.md':
        return True
    return False

def main():
    now = datetime.now()
    stale_cutoff = now - timedelta(days=STALE_DAYS)

    files = get_all_files(MEMORY_DIR)
    total_count = len(files)
    total_size = sum(f.stat().st_size for f in files)
    total_size_kb = total_size / 1024

    # Files >5KB
    large_files = [(f, f.stat().st_size) for f in files if f.stat().st_size > MAX_SIZE_KB * 1024]

    # Orphaned files (not referenced by any INDEX.md)
    index_refs = find_index_refs(MEMORY_DIR)
    orphans = []
    for f in files:
        if not is_referenced(f, index_refs, MEMORY_DIR):
            orphans.append(f)

    # Stale files (>30 days since last edit)
    stale_files = []
    for f in files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < stale_cutoff:
            stale_files.append((f, mtime))

    # Generate report
    report_date = now.strftime('%Y-%m-%d')
    lines = [
        f"# Memory Hygiene Report — {report_date}",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M')} by Scribe (memory/scribe/hygiene_report.py)",
        "",
        "## Summary Metrics",
        "",
        f"| Metric | Value | Target | Status |",
        f"|--------|-------|--------|--------|",
        f"| Total files | {total_count} | — | — |",
        f"| Total size | {total_size_kb:.1f} KB | — | — |",
        f"| Files >{MAX_SIZE_KB}KB | {len(large_files)} | 0 | {'✅' if not large_files else '⚠️'} |",
        f"| Orphaned files | {len(orphans)} | 0 | {'✅' if not orphans else '⚠️'} |",
        f"| Stale files (>30d) | {len(stale_files)} | <10% | {'✅' if len(stale_files) <= total_count*0.1 else '⚠️'} |",
        "",
    ]

    if large_files:
        lines += ["## Files >5KB (should be split)", ""]
        for f, size in sorted(large_files, key=lambda x: -x[1])[:20]:
            rel = f.relative_to(MEMORY_DIR.parent).as_posix()
            lines.append(f"- `{rel}` — {size/1024:.1f} KB")
        if len(large_files) > 20:
            lines.append(f"- ... and {len(large_files)-20} more")
        lines.append("")

    if orphans:
        lines += ["## Orphaned Files (not referenced by any INDEX.md)", ""]
        for f in sorted(orphans)[:30]:
            rel = f.relative_to(MEMORY_DIR.parent).as_posix()
            lines.append(f"- `{rel}`")
        if len(orphans) > 30:
            lines.append(f"- ... and {len(orphans)-30} more")
        lines.append("")

    if stale_files:
        lines += ["## Stale Files (>30 days no edit)", ""]
        for f, mtime in sorted(stale_files, key=lambda x: x[1])[:20]:
            rel = f.relative_to(MEMORY_DIR.parent).as_posix()
            lines.append(f"- `{rel}` — last modified {mtime.strftime('%Y-%m-%d')}")
        if len(stale_files) > 20:
            lines.append(f"- ... and {len(stale_files)-20} more")
        lines.append("")

    # Remediation list
    violations = []
    if large_files:
        violations.append(f"Split {len(large_files)} files >{MAX_SIZE_KB}KB into modules")
    if orphans:
        violations.append(f"Add INDEX.md references or archive {len(orphans)} orphaned files")
    if not violations:
        violations.append("No remediation needed — all targets met.")

    lines += ["## Remediation List", ""]
    for i, v in enumerate(violations, 1):
        lines.append(f"{i}. {v}")
    lines.append("")

    report_text = '\n'.join(lines)
    print(report_text)

    if '--write' in sys.argv:
        out_path = MEMORY_DIR / 'scribe' / f"hygiene-report-{report_date}.md"
        out_path.write_text(report_text, encoding='utf-8')
        print(f"\n[WRITTEN] {out_path.relative_to(MEMORY_DIR.parent)}")

    sys.exit(0)

if __name__ == '__main__':
    main()