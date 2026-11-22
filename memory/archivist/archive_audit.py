#!/usr/bin/env python3
"""Archive Hygiene Audit - Archivist Goal 10 tool.

Checks all files in memory/goals/archive/ and memory/archivist/archive/:
  1. Date stamp in filename (YYYY-MM-DD)
  2. Agent attribution (filename prefix OR content header)
  3. Archiving context/reason present
  4. Not truncated (reasonable size, last line looks complete)

Usage: python memory/archivist/archive_audit.py [--json]
"""
import re, json, sys
from pathlib import Path

AGENTS = {"archivist","builder","designer","mechanic","orchestrator",
          "researcher","scribe","verifier","rosterprobe"}

def audit():
    dirs = [Path("memory/goals/archive"), Path("memory/archivist/archive")]
    r = {"checked": 0, "pass": 0, "warn": 0, "fail": 0, "issues": []}
    
    for d in dirs:
        if not d.exists():
            continue
        files = sorted(d.glob("*.md")) + sorted(d.glob("*.json"))
        files = [f for f in files if f.name not in ("INDEX.md", "README.md")]
        
        for f in files:
            r["checked"] += 1
            issues = []
            
            # 1. Date stamp
            if not re.search(r'\d{4}-\d{2}-\d{2}', f.name):
                issues.append("no date stamp in filename")
            
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                r["fail"] += 1
                r["issues"].append({"file": str(f), "problems": [f"unreadable: {e}"]})
                continue
            
            # 2. Agent attribution
            stem = f.stem.lower()
            agent_in_name = any(stem.startswith(a) or a in stem.split('-')[0] for a in AGENTS)
            agent_in_content = bool(re.search(r'(?i)(\bagent\b|\bsource\b|\bprovenance\b|\bowner\b)', content[:800]))
            if not agent_in_name and not agent_in_content:
                issues.append("no agent attribution")
            
            # 3. Archiving context (directory = provenance for goals/archive)
            reason = bool(re.search(r'(?i)(supersed|archiv|closed|complete|replac|cycle \d)', content[:800]))
            if not reason and d != Path("memory/goals/archive"):
                issues.append("no archiving reason in header")
            
            # 4. Truncation
            lines = [l for l in content.split('\n') if l.strip()]
            if len(content) < 50:
                issues.append(f"too small ({len(content)} bytes)")
            elif lines:
                last = lines[-1].rstrip()
                if len(last) > 100 and not re.search(r'[\.\!\?\)\]\}`|}\-\u2026"\'\%:]$', last):
                    if '...' not in last[-5:]:
                        issues.append("possible truncation")
            
            if any('too small' in i or 'unreadable' in i for i in issues):
                r["fail"] += 1
            elif issues:
                r["warn"] += 1
            else:
                r["pass"] += 1
            
            if issues:
                r["issues"].append({"file": str(f), "problems": issues})
    
    return r

if __name__ == "__main__":
    result = audit()
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Archive Hygiene Audit: {result['pass']}/{result['checked']} PASS, "
              f"{result['warn']} WARN, {result['fail']} FAIL")
        for i in result["issues"]:
            print(f"  [{i['problems'][0][:20]}] {i['file']}")
    sys.exit(1 if result["fail"] > 0 else 0)
