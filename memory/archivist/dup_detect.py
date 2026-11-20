#!/usr/bin/env python3
"""dup_detect.py - Goal #8: Near-duplicate detection via shingling.

Usage: python memory/archivist/dup_detect.py [--threshold 0.7] [--min-shingles 30]

Finds pairs of memory/ leaves with Jaccard similarity > threshold using
5-word n-gram shingling + inverted-index blocking for efficiency.
"""
import os, json, re, sys, time, argparse
from pathlib import Path
from collections import defaultdict, Counter

MEMORY_ROOT = Path("memory")
REPORT_JSON = MEMORY_ROOT / "archivist" / "dup-detect-report-2026-11-20.json"
REPORT_MD = MEMORY_ROOT / "archivist" / "dup-detect-report-2026-11-20.md"

SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.bin', '.exe', '.dll'}
SKIP_DIRS = {'__pycache__', 'node_modules', '.git', '.kg_state'}
# Expected deployment/sync copies + browser test profiles - not knowledge dups
EXCLUDE_DIR_PATTERNS = ('canary', 'merge-queue', 'dep-snapshots')
EXCLUDE_PREFIXES = ('_ud', '_t768', '_t1024', '_t1920', '_edge_ud')

def collect_leaves():
    leaves = []
    for dirpath, dirnames, filenames in os.walk(MEMORY_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if ext in SKIP_EXT:
                continue
            p = Path(dirpath) / fn
            # Skip expected copy dirs
            if any(part in EXCLUDE_DIR_PATTERNS for part in p.parts):
                continue
            # Skip browser profile test artifacts
            if any(part.startswith(EXCLUDE_PREFIXES) for part in p.parts):
                continue
            try:
                if p.stat().st_size > 500_000:
                    continue
            except OSError:
                continue
            leaves.append(p)
    return leaves

def text_shingles(text, n=5):
    words = re.findall(r'[a-z0-9]+', text.lower())
    if len(words) < n:
        return set(words) if words else set()
    return {' '.join(words[i:i+n]) for i in range(len(words) - n + 1)}

def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--threshold', type=float, default=0.7)
    ap.add_argument('--min-shingles', type=int, default=30)
    args = ap.parse_args()
    
    t0 = time.time()
    leaves = collect_leaves()
    print(f"Scanning {len(leaves)} leaf files...")
    
    shingles = {}
    inverted = defaultdict(set)
    
    for p in leaves:
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except (OSError, UnicodeDecodeError):
            continue
        if len(text.strip()) < 100:
            continue
        s = text_shingles(text)
        if len(s) < args.min_shingles:
            continue
        key = str(p).replace('\\', '/')
        shingles[key] = s
        for sh in s:
            inverted[sh].add(key)
    
    print(f"Eligible: {len(shingles)} files, {len(inverted)} unique shingles")
    
    # Blocking via inverted index
    candidates = defaultdict(int)
    for sh, files in inverted.items():
        if len(files) < 2:
            continue
        flist = list(files)
        for i in range(len(flist)):
            for j in range(i + 1, len(flist)):
                pair = (flist[i], flist[j]) if flist[i] < flist[j] else (flist[j], flist[i])
                candidates[pair] += 1
    
    print(f"Candidate pairs: {len(candidates)}")
    
    pairs = []
    for (a, b), shared in candidates.items():
        sa, sb = len(shingles[a]), len(shingles[b])
        if shared < 0.4 * min(sa, sb):
            continue
        sim = jaccard(shingles[a], shingles[b])
        if sim > args.threshold:
            pairs.append({
                "file_a": a,
                "file_b": b,
                "jaccard": round(sim, 4),
                "shingles_a": sa,
                "shingles_b": sb,
                "shared_shingles": shared
            })
    
    pairs.sort(key=lambda x: -x["jaccard"])
    elapsed = time.time() - t0
    print(f"Found {len(pairs)} pairs with Jaccard > {args.threshold} in {elapsed:.1f}s")
    
    # Categorize + recommend
    for p in pairs:
        a_path = Path(p["file_a"])
        b_path = Path(p["file_b"])
        
        if "archive" in a_path.parts or "archive" in b_path.parts:
            keep = p["file_b"] if "archive" in a_path.parts else p["file_a"]
            p["category"] = "archive-dup"
            p["action"] = f"Keep `{keep}`; add pointer from archived copy"
        elif a_path.parent == b_path.parent:
            p["category"] = "same-dir"
            p["action"] = f"CROSS-REF or MERGE in {a_path.parent}"
        else:
            p["category"] = "cross-dir"
            p["action"] = f"CROSS-REF: add pointer lines in both files"
    
    # Write JSON (full)
    report = {
        "method": "shingling (5-word n-grams) + inverted-index blocking",
        "threshold": args.threshold,
        "min_shingles_per_file": args.min_shingles,
        "excluded_patterns": list(EXCLUDE_DIR_PATTERNS) + list(EXCLUDE_PREFIXES),
        "files_scanned": len(leaves),
        "files_eligible": len(shingles),
        "unique_shingles": len(inverted),
        "candidate_pairs_blocked": len(candidates),
        "pairs_found": len(pairs),
        "pairs": pairs,
        "runtime_seconds": round(elapsed, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    
    # Write MD summary
    cat_counts = Counter(p["category"] for p in pairs)
    lines = [
        "# Duplication Detection Report",
        f"Date: 2026-11-20 | Agent: Archivist | Goal: #8",
        "",
        f"**Method:** 5-word n-gram shingling, Jaccard > {args.threshold}, inverted-index blocking",
        f"**Coverage:** {len(leaves)} files scanned → {len(shingles)} eligible; deployment/test dirs excluded",
        f"**Runtime:** {elapsed:.1f}s",
        "",
        f"## Result: {len(pairs)} near-duplicate pair(s)",
        "",
        "| Category | Count |",
        "|----------|-------|"
    ]
    for cat, cnt in cat_counts.most_common():
        lines.append(f"| {cat} | {cnt} |")
    
    lines += ["", "## Top 10 Pairs", ""]
    for k, p in enumerate(pairs[:10], 1):
        lines.append(f"{k}. **J={p['jaccard']}** [{p['category']}] `{p['file_a']}` ↔ `{p['file_b']}`")
    
    lines += ["", "---", "*Generated by `dup_detect.py` (Goal #8, cycle-8)*"]
    REPORT_MD.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Reports: {REPORT_JSON}, {REPORT_MD}")

if __name__ == "__main__":
    main()
