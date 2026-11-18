#!/usr/bin/env python3
"""lint_reports.py - Verify all Verifier reports conform to canonical format.
Usage: python memory/verifier/lint_reports.py
"""
import os, re, sys
from datetime import datetime

REQUIRED = ["date", "suite", "pass", "fail", "total", "evidence_path"]
VERIFIER_DIR = os.path.join(os.path.dirname(__file__))

def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1: return None
    fields = {}
    for line in text[3:end].strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields

def main():
    ok, bad = 0, 0
    for fname in sorted(os.listdir(VERIFIER_DIR)):
        if not fname.endswith(".md"): continue
        fp = os.path.join(VERIFIER_DIR, fname)
        with open(fp, encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        if fm is None: continue  # skip non-report files
        issues = []
        for field in REQUIRED:
            if field not in fm: issues.append(f"missing:{field}")
        if "date" in fm:
            try: datetime.fromisoformat(fm["date"].replace("Z","+00:00"))
            except: issues.append("bad-date")
        if all(k in fm for k in ["pass","fail","total"]):
            try:
                if int(fm["pass"])+int(fm["fail"]) != int(fm["total"]):
                    issues.append("arithmetic")
            except: pass
        if issues:
            bad += 1
            print(f"FAIL {fname}: {', '.join(issues)}")
        else:
            ok += 1
    print(f"\n{ok} conform / {bad} non-conform")
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
