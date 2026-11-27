#!/usr/bin/env python3
"""Verification Coverage Map (Verifier Goal #7)
Enumerates all tracked files in the portal and classifies each as:
  - verified: an evidence artifact referencing this file exists and is <48h old
  - stale-verified: evidence exists but >48h old
  - unverified: no evidence artifact found

Output: memory/verifier/verification-coverage-map.json + .md summary
"""
import json, os, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "memory" / "verifier"
STALE_HOURS = 48

# File extensions we track as "portal files"
TRACKED_EXTS = {".py", ".js", ".css", ".html", ".json", ".md", ".sh"}
EXCLUDE_DIRS = {"__pycache__", "archive", "_archived", "node_modules", ".git"}

def enumerate_files():
    """Walk the portal and collect all tracked files."""
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in TRACKED_EXTS:
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                files.append(rel)
    return sorted(files)

def find_evidence_for_file(filepath):
    """Search evidence artifacts for mentions of this file path.
    Returns the most recent evidence timestamp or None."""
    if not EVIDENCE_DIR.exists():
        return None
    
    # Normalize: try both slash and backslash forms, also just basename
    basename = os.path.basename(filepath)
    
    best_ts = None
    for ev_file in EVIDENCE_DIR.iterdir():
        if not ev_file.suffix == ".md":
            continue
        try:
            content = ev_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        
        # Check if this file is mentioned (full relative path or basename)
        if filepath in content or basename in content:
            # Use the evidence file's mtime as the verification timestamp
            ts = datetime.fromtimestamp(ev_file.stat().st_mtime, tz=timezone.utc)
            if best_ts is None or ts > best_ts:
                best_ts = ts
    
    return best_ts

def classify(filepath):
    """Return (status, last_verified_ts)."""
    ts = find_evidence_for_file(filepath)
    if ts is None:
        return "unverified", None
    age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    if age_hours > STALE_HOURS:
        return "stale-verified", ts
    return "verified", ts

def main():
    print("Enumerating portal files...")
    all_files = enumerate_files()
    print(f"  Found {len(all_files)} tracked files")
    
    print("Classifying each file...")
    results = []
    for f in all_files:
        status, ts = classify(f)
        results.append({"file": f, "status": status, "last_verified": ts.isoformat() if ts else None})
    
    # Compute stats
    counts = {"verified": 0, "stale-verified": 0, "unverified": 0}
    for r in results:
        counts[r["status"]] += 1
    
    total = len(results)
    verified_pct = (counts["verified"] + counts["stale-verified"]) / total * 100 if total else 0
    strictly_verified_pct = counts["verified"] / total * 100 if total else 0
    
    print(f"\nResults:")
    print(f"  Total files: {total}")
    print(f"  Verified: {counts['verified']} ({strictly_verified_pct:.1f}%)")
    print(f"  Stale-verified: {counts['stale-verified']}")
    print(f"  Unverified: {counts['unverified']}")
    print(f"  Coverage (verified + stale): {verified_pct:.1f}%")
    
    # Gap list: unverified files ranked by directory (most critical first)
    gaps = [r for r in results if r["status"] == "unverified"]
    # Sort: .py and .js first (code), then others
    def gap_priority(r):
        ext = os.path.splitext(r["file"])[1]
        return 0 if ext in (".py", ".js") else 1
    gaps.sort(key=gap_priority)
    
    # Write JSON output
    out_json = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_files": total,
        "counts": counts,
        "verified_pct": round(verified_pct, 2),
        "strictly_verified_pct": round(strictly_verified_pct, 2),
        "stale_threshold_hours": STALE_HOURS,
        "gaps": gaps[:50],  # top 50 unverified files
        "all_files": results
    }
    
    json_path = EVIDENCE_DIR / "verification-coverage-map.json"
    json_path.write_text(json.dumps(out_json, indent=2), encoding="utf-8")
    print(f"\nJSON written: {json_path.name}")
    
    # Write markdown summary
    md_lines = [
        "# Verification Coverage Map",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total tracked files | {total} |",
        f"| Verified (<{STALE_HOURS}h) | {counts['verified']} ({strictly_verified_pct:.1f}%) |",
        f"| Stale-verified (>{STALE_HOURS}h) | {counts['stale-verified']} |",
        f"| Unverified | {counts['unverified']} |",
        f"| **Overall coverage** | **{verified_pct:.1f}%** |",
        "",
        "## Top Gaps (unverified code files first)",
        "",
    ]
    for g in gaps[:20]:
        md_lines.append(f"- `{g['file']}`")
    
    md_path = EVIDENCE_DIR / "verification-coverage-map.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"MD written: {md_path.name}")
    
    # Exit 0 if >=90% coverage (goal target)
    if verified_pct >= 90:
        print(f"\nRESULT: PASS | {verified_pct:.1f}% >= 90% target")
        return 0
    else:
        print(f"\nRESULT: INFO | {verified_pct:.1f}% < 90% target ({counts['unverified']} files unverified)")
        return 0  # Still successful run, just below target

if __name__ == "__main__":
    sys.exit(main())
