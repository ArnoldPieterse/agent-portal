"""Scribe compression quality gate - auto-lint before recording.
Usage: python memory/scribe/compression_lint.py <file_or_stdin>
Exit 0 = pass, Exit 1 = errors found (warns do not block).
"""
import os, re, sys, json
from datetime import datetime

ROSTER = {"Orchestrator", "Researcher", "Builder", "Verifier", "Designer", "Archivist", "Mechanic", "Scribe"}

def lint_scribe_output(text):
    violations = []
    lines = text.strip().split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        # R1: Source citation check
        has_citation = bool(
            re.search(r'memory/[^\s\)\]\|]+', stripped) or
            re.search(r'\(pointer:', stripped) or
            re.search(r'verified[:\s]', stripped, re.I) or
            re.search(r'(Orchestrator|Researcher|Builder|Verifier|Designer|Archivist|Mechanic|Scribe)\s*#?\d+', stripped) or
            re.search(r'\[DM\s+@', stripped) or
            re.search(r'cites?[:\s]', stripped, re.I)
        )
        if not has_citation and len(stripped) > 20:
            violations.append({"line": i, "rule": "R1", "severity": "warn",
                "message": f"No source citation found: {stripped[:80]}..."})
        # R3: File path existence
        for match in re.finditer(r'(memory/[^\s\)\]\|,]+)', stripped):
            fpath = match.group(1).rstrip('.').replace("\\", "/")
            if '*' not in fpath and '<' not in fpath and '...' not in fpath:
                if not os.path.exists(fpath):
                    violations.append({"line": i, "rule": "R3", "severity": "error",
                        "message": f"Path does not exist: {fpath}"})
        # R4: Agent name check
        for match in re.finditer(r'\b([A-Z][a-z]+)\s+#\d+', stripped):
            name = match.group(1)
            if name not in ROSTER and name not in ('The', 'This', 'That', 'Goal', 'Round', 'Cycle', 'Task', 'Item', 'Step', 'Phase', 'Lane'):
                violations.append({"line": i, "rule": "R4", "severity": "warn",
                    "message": f"Unknown agent name: {name}"})
    # R2: Numeric consistency
    for match in re.finditer(r'(\d+)/(\d+)', text):
        num, den = int(match.group(1)), int(match.group(2))
        if num > den:
            violations.append({"line": 0, "rule": "R2", "severity": "error",
                "message": f"Fraction {num}/{den} has numerator > denominator"})
    return violations

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    
    violations = lint_scribe_output(text)
    errors = [v for v in violations if v['severity'] == 'error']
    warns = [v for v in violations if v['severity'] == 'warn']
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_violations": len(violations),
        "errors": len(errors),
        "warnings": len(warns),
        "pass": len(errors) == 0,
        "violations": violations
    }
    print(json.dumps(report, indent=2))
    
    # Log to evidence ledger
    log_path = "memory/scribe/compression-lint-log.jsonl"
    with open(log_path, 'a') as f:
        f.write(json.dumps(report) + '\n')
    
    sys.exit(0 if not errors else 1)
