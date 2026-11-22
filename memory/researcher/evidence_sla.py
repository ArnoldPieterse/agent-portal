#!/usr/bin/env python3
"""Evidence Freshness SLA - scans memory/**/*.md for stale evidence leaves.

Stale = file not updated (by mtime or internal timestamp) in >7 days AND
lacks a "verified:" or "(progress)" marker in its body.

Usage: python memory/researcher/evidence_sla.py [--days N] [--output PATH]
"""
import os, re, sys, json
from datetime import datetime, timedelta
from pathlib import Path

def extract_internal_timestamps(text):
    """Extract the most recent date found in the file body (YYYY-MM-DD pattern)."""
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', text)
    valid = []
    for d in dates:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            # Ignore future dates (likely template placeholders)
            if dt <= datetime.now():
                valid.append(dt)
        except ValueError:
            pass
    return max(valid) if valid else None

def is_stale(path, threshold_days):
    """Check if a file is stale."""
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except Exception as e:
        return False, f"read error: {e}", None, None

    # Check for freshness markers in body
    has_verified = bool(re.search(r'verified:', text))
    has_progress = bool(re.search(r'\(progress\)', text))
    
    if has_verified or has_progress:
        return False, "has freshness marker", mtime, None

    # Determine effective last-update: max of mtime and any internal timestamp
    internal_ts = extract_internal_timestamps(text)
    effective_update = max(mtime, internal_ts) if internal_ts else mtime
    
    age_days = (datetime.now() - effective_update).days
    is_old = age_days > threshold_days
    
    return is_old, f"age={age_days}d", mtime, effective_update

def main():
    days_threshold = 7
    output_path = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i+1 < len(args):
            days_threshold = int(args[i+1])
            i += 2
        elif args[i] == "--output" and i+1 < len(args):
            output_path = args[i+1]
            i += 1
        else:
            i += 1
    
    # Default output path
    today = datetime.now().strftime("%Y-%m-%d")
    if not output_path:
        output_path = f"memory/ops/evidence-stale-{today}.md"
    
    # Walk memory/**/*.md
    base = Path("memory")
    if not base.exists():
        print(f"ERROR: {base} does not exist", file=sys.stderr)
        sys.exit(1)
    
    md_files = sorted(base.rglob("*.md"))
    stale = []
    fresh = []
    errors = []
    skipped_non_leaf = 0
    
    for f in md_files:
        # Skip index files and goal files (not evidence leaves)
        name = f.name.lower()
        if name in ("index.md", "memory.md") or "goals" in str(f).lower():
            skipped_non_leaf += 1
            continue
        
        is_st, reason, mtime, eff_ts = is_stale(str(f), days_threshold)
        if is_st:
            stale.append({
                "path": str(f),
                "reason": reason,
                "mtime": mtime.strftime("%Y-%m-%d %H:%M") if mtime else None,
                "effective_update": eff_ts.strftime("%Y-%m-%d") if eff_ts else None
            })
        else:
            fresh.append({"path": str(f), "reason": reason})
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"# Evidence Freshness SLA Report - {today}\n\n")
        out.write(f"Threshold: {days_threshold} days\n")
        out.write(f"Scanned: {len(md_files)} files (skipped {skipped_non_leaf} non-leaf)\n")
        out.write(f"STALE: {len(stale)} | Fresh: {len(fresh)}\n\n")
        
        if stale:
            out.write("## STALE Files (>{}d, no freshness marker)\n\n".format(days_threshold))
            for s in sorted(stale, key=lambda x: x["path"]):
                out.write(f"- `{s['path']}` - {s['reason']} (mtime: {s['mtime']})\n")
            out.write("\n")
        
        out.write("## Fresh Files (have marker or recent)\n\n")
        for f in fresh[:50]:  # cap for readability
            out.write(f"- `{f['path']}` - {f['reason']}\n")
        if len(fresh) > 50:
            out.write(f"  ... and {len(fresh)-50} more\n")
    
    print(f"Report written to {output_path}")
    print(f"STALE={len(stale)} FRESH={len(fresh)} SKIPPED={skipped_non_leaf}")
    
    # Exit code: 0 if clean, 1 if stale found (for CI-style use)
    sys.exit(0 if len(stale) == 0 else 1)

if __name__ == "__main__":
    main()
