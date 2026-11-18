"""Scribe #8 - Compression quality gate.
Pre-commit lint for Scribe outputs: checks for missing citations, vague language,
unverified numbers. Exits 0 if clean, 1 if violations found (blocks commit).

Usage: python memory/scribe/compression_gate.py <file_or_dir>
"""
import os, re, sys, glob

# Vague language patterns that weaken a synthesis bullet
VAGUE_PATTERNS = [
    (r'\bsome\b', 'vague quantifier "some" - use exact count or "all/none"'),
    (r'\bvarious\b', 'vague "various" - name the specific items'),
    (r'\ba few\b', 'vague "a few" - use exact count'),
    (r'\bseveral\b', 'vague "several" - use exact count'),
    (r'\betc\.?\b', '"etc." implies incomplete enumeration - list all or say "among others" with count'),
    (r'\bin general\b', '"in general" is too vague for a decision record - be specific'),
    (r'\bas usual\b', '"as usual" assumes context not in the record - state what happened'),
    (r'\btypically\b', '"typically" implies unverified pattern - cite the source or remove'),
]

# A number that appears without a date, source, or "verified:" marker nearby
UNVERIFIED_NUM_PATTERN = re.compile(
    r'(?<![:\d])(\d{2,})(?![\d:/%])'  # 2+ digit numbers not part of time/percent/path
)

# Citation patterns that count as verified sources
CITATION_PATTERNS = [
    r'verified:', r'source:', r'evidence:', r'pointer:',
    r'exit code', r'PID \d+', r'\d{4}-\d{2}-\d{2}',  # dates count as temporal anchors
]

def check_file(filepath):
    """Check a single file for compression quality violations. Returns list of (line_num, msg)."""
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return [(0, f'cannot read {filepath}')]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip empty lines, headers, horizontal rules
        if not stripped or stripped.startswith('#') or stripped == '---':
            continue
        # Skip lines that are clearly metadata (JSON keys, code)
        if stripped.startswith('{') or stripped.startswith('}') or stripped.startswith('"'):
            continue

        # Check vague language
        for pattern, msg in VAGUE_PATTERNS:
            if re.search(pattern, line, re.I):
                violations.append((i, f'vague: {msg}'))

        # Check unverified numbers (only in bullet/decision lines)
        if stripped.startswith('-') or 'DECIDED' in line.upper() or 'owner:' in line:
            has_citation = any(re.search(cp, line, re.I) for cp in CITATION_PATTERNS)
            if not has_citation:
                nums = UNVERIFIED_NUM_PATTERN.findall(line)
                # Filter out numbers that are clearly part of filenames/paths/times
                real_nums = [n for n in nums if not re.search(rf'{n}/|\.{n}\b|:{n}\b', line)]
                if real_nums:
                    violations.append((i, f'unverified number(s) {real_nums[:3]} without date/source/verified marker'))

    return violations

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/scribe/compression_gate.py <file_or_dir>")
        sys.exit(2)

    target = sys.argv[1]
    files = []
    if os.path.isdir(target):
        for ext in ('*.md', '*.json'):
            files.extend(glob.glob(os.path.join(target, '**', ext), recursive=True))
    elif os.path.isfile(target):
        files = [target]
    else:
        print(f"ERROR: {target} not found")
        sys.exit(2)

    all_violations = []
    for f in files:
        v = check_file(f)
        if v:
            all_violations.append((f, v))

    if all_violations:
        total = sum(len(v) for _, v in all_violations)
        print(f"COMPRESSION GATE: FAIL - {total} violation(s) in {len(all_violations)} file(s)")
        for filepath, violations in all_violations:
            print(f"\n  {filepath}:")
            for line_num, msg in violations[:10]:  # cap display
                print(f"    L{line_num}: {msg}")
            if len(violations) > 10:
                print(f"    ... and {len(violations)-10} more")
        sys.exit(1)
    else:
        print(f"COMPRESSION GATE: PASS - {len(files)} file(s) checked, 0 violations")
        sys.exit(0)

if __name__ == '__main__':
    main()
