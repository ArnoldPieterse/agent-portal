#!/usr/bin/env python3
"""contradiction_detector.py - Cross-check a round's claims vs disk ground truth.

Usage:
  python contradiction_detector.py --claims claims.json [--root .]

claims.json format:
[
  {"id": "c1", "type": "line_count", "target": "MEMORY.md", "expected": 31},
  {"id": "c2", "type": "file_size",   "target": "agent_portal.py", "expected": 48200, "tolerance": 500},
  {"id": "c3", "type": "sha256",      "target": "TODO.md", "expected": "abc123..."},
  {"id": "c4", "type": "count",       "target": "memory/", "pattern": "*.md", "expected": 462},
  {"id": "c5", "type": "exists",      "target": "memory/goals/scribe.md", "expected": true}
]

Exit code: 0 = all pass, 1 = at least one FAIL.
Output: JSON to stdout with per-claim results + summary.
"""
import json, os, hashlib, sys
from pathlib import Path

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def check_claim(claim, root):
    cid   = claim.get("id", "?")
    ctype = claim["type"]
    # v2 types don't always have target/expected at top level
    target_str = claim.get("target", claim.get("index_file", claim.get("file_a", "?")))
    target = Path(root) / target_str
    expected = claim.get("expected")
    tol     = claim.get("tolerance", 0)

    result = {"id": cid, "type": ctype, "target": str(target_str)}
    if expected is not None:
        result["expected"] = expected

    try:
        # --- v2 types ---
        if ctype == "temporal_mismatch":
            from datetime import datetime, timezone
            claimed_date = claim["claimed_date"]
            tol_days = claim.get("tolerance_days", 0)
            mtime = target.stat().st_mtime
            mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            claimed_dt = datetime.fromisoformat(claimed_date).replace(tzinfo=timezone.utc)
            diff_days = abs((mtime_dt - claimed_dt).total_seconds()) / 86400
            result["actual_mtime"] = mtime_dt.isoformat()
            result["diff_days"] = round(diff_days, 2)
            result["pass"] = diff_days <= tol_days

        elif ctype == "cross_reference":
            import re as _re
            fa = Path(root) / claim["file_a"]
            fb = Path(root) / claim["file_b"]
            pa = claim.get("pattern_a", ".")
            pb = claim.get("pattern_b", ".")
            ca = len(_re.findall(pa, fa.read_text(encoding='utf-8', errors='replace')))
            cb = len(_re.findall(pb, fb.read_text(encoding='utf-8', errors='replace')))
            result["count_a"] = ca
            result["count_b"] = cb
            result["pass"] = (ca == cb)

        elif ctype == "stale_pointer":
            import re as _re
            idx_file = Path(root) / claim["index_file"]
            ppat = claim.get("pointer_pattern", r"->\s+(memory/[^\s]+\.md)")
            text = idx_file.read_text(encoding='utf-8', errors='replace')
            pointers = _re.findall(ppat, text)
            stale = []
            for p in pointers:
                # handle both full match and group(1)
                pp = p if isinstance(p, str) else p[0]
                fp = Path(root) / pp
                if not fp.exists():
                    stale.append(pp)
            result["total_pointers"] = len(pointers)
            result["stale_count"] = len(stale)
            if stale:
                result["stale_samples"] = stale[:5]
            result["pass"] = len(stale) == 0

        elif ctype == "size_drift":
            claimed_kb = claim["claimed_kb"]
            pct_tol = claim.get("pct_tolerance", 10)
            actual_kb = target.stat().st_size / 1024.0
            drift_pct = abs(actual_kb - claimed_kb) / claimed_kb * 100 if claimed_kb > 0 else 999
            result["actual_kb"] = round(actual_kb, 2)
            result["drift_pct"] = round(drift_pct, 1)
            result["pass"] = drift_pct <= pct_tol

        elif ctype == "duplicate_entry":
            entry_str = claim["entry"]
            max_occ = claim.get("max_occurrences", 1)
            text = target.read_text(encoding='utf-8', errors='replace')
            occ = text.count(entry_str)
            result["occurrences"] = occ
            result["max_allowed"] = max_occ
            result["pass"] = occ <= max_occ

        # --- v1 types ---
        elif ctype == "line_count":
            actual = len(target.read_text().splitlines())
            result["actual"] = actual
            result["pass"] = abs(actual - expected) <= tol

        elif ctype == "file_size":
            actual = target.stat().st_size
            result["actual"] = actual
            result["pass"] = abs(actual - expected) <= tol

        elif ctype == "sha256":
            actual = sha256_file(target)
            result["actual"] = actual[:16] + "..."
            result["pass"] = actual.startswith(expected) or actual == expected

        elif ctype == "count":
            pattern = claim.get("pattern", "*")
            files = list(target.rglob(pattern)) if target.is_dir() else [target.parent / pattern]
            # rglob on a dir; if target is a file, count=1
            if target.is_file():
                actual = 1
            else:
                actual = len(list(target.rglob(pattern)))
            result["actual"] = actual
            result["pass"] = abs(actual - expected) <= tol

        elif ctype == "exists":
            actual = target.exists()
            result["actual"] = actual
            result["pass"] = (actual == expected)

        else:
            result["pass"] = False
            result["error"] = f"unknown claim type: {ctype}"

    except FileNotFoundError as e:
        # For stale_pointer, a missing index file is itself a failure
        if ctype == "stale_pointer":
            result["actual"] = None
            result["pass"] = False
            result["error"] = f"index file not found: {claim.get('index_file','?')}"
        else:
            result["actual"] = None
            result["pass"] = False
            result["error"] = "file not found"
        result["actual"] = None
        result["pass"] = False
        result["error"] = "file not found"
    except Exception as e:
        result["actual"] = None
        result["pass"] = False
        result["error"] = str(e)

    return result

def main():
    import argparse
    p = argparse.ArgumentParser(description="Contradiction detector")
    p.add_argument("--claims", required=True, help="Path to claims JSON file")
    p.add_argument("--root", default=".", help="Root directory for relative targets")
    args = p.parse_args()

    with open(args.claims) as f:
        claims = json.load(f)

    results = [check_claim(c, args.root) for c in claims]
    passed  = sum(1 for r in results if r["pass"])
    failed  = len(results) - passed

    report = {
        "total":  len(results),
        "passed": passed,
        "failed": failed,
        "claims": results,
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
