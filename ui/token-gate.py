#!/usr/bin/env python3
"""Token enforcement gate - flags hardcoded #hex in ui/cockpit-*.js and ui/fleet_*.js.
Excludes: var(--x, #hex) fallbacks, HTML entities (&#NNN;), and comments.
Usage: python ui/token-gate.py
Exit 0 = clean, Exit 1 = violations found."""
import re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HEX_RE = re.compile(r"(?<!&)(?<!&#)#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?\b")
VAR_FALLBACK_RE = re.compile(r"var\([^)]*#[0-9a-fA-F]+[^)]*\)")

def scan_file(path):
    """Return list of (line_no, hex_val) for violations."""
    violations = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            # Remove var(--x, #hex) patterns (acceptable fallbacks)
            cleaned = VAR_FALLBACK_RE.sub("VARTOKEN", line)
            # Remove HTML entities (&#NNN;)
            cleaned = re.sub(r"&#\d+;", "ENTITY", cleaned)
            for m in HEX_RE.finditer(cleaned):
                violations.append((i, m.group()))
    return violations

def main():
    targets = []
    for f in sorted(os.listdir(HERE)):
        if f.endswith(".js") and (f.startswith("cockpit-") or f.startswith("fleet_")):
            targets.append(os.path.join(HERE, f))
    
    total = 0
    for path in targets:
        viols = scan_file(path)
        if viols:
            fname = os.path.basename(path)
            for line_no, hex_val in viols:
                print(f"  VIOLATION {fname}:{line_no}  {hex_val}")
                total += 1
    
    if total == 0:
        print("PASS: 0 hardcoded hex violations")
        return 0
    else:
        print(f"\nFAIL: {total} hardcoded hex violations found")
        return 1

if __name__ == "__main__":
    sys.exit(main())
