#!/usr/bin/env python3
"""Fleet Memory Compression.

Identifies redundant/overlapping knowledge across agents (same fact stated in 3+ places)
and proposes consolidation into a single canonical source.

Usage: python memory/researcher/memory_compress.py [--json]
Output: memory/researcher/memory-compression-report.md
"""
import pathlib, re, json, sys
from datetime import datetime
from collections import defaultdict

MEM_DIR = pathlib.Path('memory')
OUT_PATH = pathlib.Path('memory/researcher/memory-compression-report.md')

CLAIM_PATTERNS = [
    (r'(\d+)\s*GB\s*(?:VRAM|RAM|memory)', 'resource'),
    (r'port\s*(\d{4,5})', 'port'),
    (r'(?:runs?|running|loaded on|resides on)\s+(?:a\s+)?(White|Red|Blue|Green|Yellow|Purple)', 'residency'),
    (r'(?:host|Host)\s+(\w+)\s+(?:has|with)\s+(\d+)\s*GB', 'host_spec'),
]


def extract_claims():
    """Scan all memory .md files and extract factual claims with locations."""
    claims = defaultdict(list)
    files_scanned = 0
    for f in MEM_DIR.rglob('*.md'):
        try:
            txt = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        files_scanned += 1
        rel = str(f.relative_to(pathlib.Path('.'))).replace('\\', '/')
        for pat, claim_type in CLAIM_PATTERNS:
            for m in re.finditer(pat, txt):
                if claim_type == 'host_spec':
                    val = "%s %sGB" % (m.group(1), m.group(2))
                elif claim_type == 'residency':
                    val = m.group(1)
                else:
                    val = m.group(1) if m.groups() else m.group(0)
                key = (claim_type, val.lower()[:30])
                if rel not in claims[key]:
                    claims[key].append(rel)
    return claims, files_scanned


def suggest_canonical(claim_type):
    suggestions = {
        'resource': 'memory/fleet/residency-matrix.md (hardware specs)',
        'port': 'memory/ops/network-config.md (canonical port assignments)',
        'residency': 'memory/fleet/residency-matrix.md (model-to-host bindings)',
        'host_spec': 'memory/fleet/host-specs.md (hardware inventory)',
    }
    return suggestions.get(claim_type, 'TBD - needs manual categorization')


def find_redundancies(claims, min_count=3):
    redundant = {}
    for (ctype, cval), locations in claims.items():
        if len(locations) >= min_count:
            key = "%s:%s" % (ctype, cval)
            redundant[key] = {
                'type': ctype,
                'value': cval,
                'count': len(locations),
                'locations': locations[:10],
                'suggestion': suggest_canonical(ctype)
            }
    return redundant


def build_report(redundant, files_scanned):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    r = "# Memory Compression Report\n"
    r += "Generated: %s\n" % now
    r += "Scanned: %d .md files in memory/\n" % files_scanned
    r += "Redundant claims (3+ locations): %d\n\n" % len(redundant)
    r += "## Findings and Consolidation Proposals\n\n"

    for key, info in sorted(redundant.items(), key=lambda x: -x[1]['count']):
        t = info['type']
        v = info['value']
        c = info['count']
        r += "### %s: [%s] (%d locations)\n" % (t, v, c)
        r += "- Canonical source: %s\n" % info['suggestion']
        r += "- Current duplicates:\n"
        for loc in info['locations']:
            r += "  - %s\n" % loc
        r += "\nAction: Consolidate into canonical source; replace others with pointer.\n\n"

    total_savings = sum(i['count'] - 1 for i in redundant.values())
    r += "## Compression Impact\n"
    r += "- Removing redundant restatements saves ~%d lines across the tree.\n" % total_savings
    r += "- %d facts would each have a single canonical home.\n" % len(redundant)
    return r


def self_test():
    claims, files = extract_claims()
    assert files > 100, "Expected >100 files scanned, got %d" % files
    assert len(claims) > 5, "Expected >5 claim types, got %d" % len(claims)
    redundant = find_redundancies(claims)
    assert len(redundant) >= 1, "Should find at least 1 redundant fact"
    for info in redundant.values():
        assert info['count'] >= 3
        assert info['suggestion'] and 'TBD' not in info['suggestion'] or info['type'] not in ('resource','port','residency','host_spec')
    return True


def main():
    json_out = '--json' in sys.argv
    self_test()
    claims, files_scanned = extract_claims()
    redundant = find_redundancies(claims)
    report = build_report(redundant, files_scanned)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report, encoding='utf-8')
    if json_out:
        print(json.dumps(redundant, indent=2))
    else:
        print("Report: %s (%db)" % (OUT_PATH, OUT_PATH.stat().st_size))
        print("Redundant claims found: %d" % len(redundant))
        print("Self-test: ALL PASS")


if __name__ == '__main__':
    main()
