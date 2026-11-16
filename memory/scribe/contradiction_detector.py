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
    target = Path(root) / claim["target"]
    expected = claim["expected"]
    tol     = claim.get("tolerance", 0)

    result = {"id": cid, "type": ctype, "target": str(claim["target"]), "expected": expected}

    try:
        if ctype == "line_count":
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

    except FileNotFoundError:
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
