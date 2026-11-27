#!/usr/bin/env python3
"""design_token_lint.py — Companion script for design-token-lint-workflow.md.
Lints ui/tokens.css: checks all tokens are defined, no orphan references in app.css/core.js.
Exit: 0=clean, 1=violations found.
"""
import re, sys, json
from pathlib import Path

def main():
    tokens_path = Path("ui/tokens.css")
    if not tokens_path.exists():
        print(json.dumps({"status": "FAIL", "error": "ui/tokens.css not found"}))
        sys.exit(1)
    
    tokens_text = tokens_path.read_text(encoding="utf-8")
    # Extract defined custom properties
    defined = set(re.findall(r'--([a-z][\w-]*)\s*:', tokens_text))
    
    violations = []
    # Check app.css for references to undefined tokens
    for css_file in ["ui/app.css", "ui/core.js"]:
        p = Path(css_file)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        referenced = set(re.findall(r'var\(--([a-z][\w-]*)', text))
        undefined = referenced - defined
        if undefined:
            violations.append({"file": css_file, "undefined_tokens": sorted(undefined)})
    
    if violations:
        print(json.dumps({"status": "DRIFT", "defined_tokens": len(defined), "violations": violations}, indent=2))
        sys.exit(1)
    print(json.dumps({"status": "CLEAN", "tokens_defined": len(defined)}))
    sys.exit(0)

if __name__ == "__main__":
    main()
