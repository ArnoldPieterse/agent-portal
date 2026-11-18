"""check_doc_file_refs.py - Archivist #5: Multi-host doc consistency v2
Scans memory/ops/*.md for file path references and flags phantoms (refs to non-existent files).
Usage: python check_doc_file_refs.py [--json]
"""
import os, re, sys, json

# Known directory prefixes + bare filenames with extensions
PATH_RE = re.compile(
    r'(?<![\w/])'
    r'((?:memory|ui|ops|agents|scripts)/[A-Za-z0-9_\-./]+)'
    r'|'
    r'([A-Za-z][A-Za-z0-9_\-]*\.(?:py|json|md|css|js|html|yaml|yml|toml))'
)

# Patterns that indicate template/placeholder (not real refs)
TEMPLATE_PATTERNS = re.compile(
    r'(NNN|YYYY|path-to-file|does-not-exist|_result\.|ref\.json|TODO_done_part)'
)

def extract_refs(text):
    refs = set()
    for line in text.splitlines():
        if line.strip().startswith(('http://', 'https://')):
            continue
        for m in PATH_RE.finditer(line):
            ref = (m.group(1) or m.group(2)).strip()
            ref = ref.rstrip('.,;:)]}\'>'')
            # Skip templates and very short refs
            if len(ref) > 4 and not ref.startswith('..'):
                if not TEMPLATE_PATTERNS.search(ref):
                    refs.add(ref)
    return refs

def main():
    ops_dir = 'memory/ops'
    all_refs = {}
    
    for fname in sorted(os.listdir(ops_dir)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(ops_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('http://', 'https://')):
                continue
            for m in PATH_RE.finditer(line):
                ref = (m.group(1) or m.group(2)).strip()
                ref = ref.rstrip('.,;:)]}\'>'')
                if len(ref) > 4 and not ref.startswith('..'):
                    if not TEMPLATE_PATTERNS.search(ref):
                        all_refs.setdefault(ref, []).append((fname, i))
    
    phantom = {}
    existing = {}
    for ref, occurrences in sorted(all_refs.items()):
        norm = ref.replace('/', os.sep)
        if os.path.exists(norm):
            existing[ref] = occurrences
        else:
            phantom[ref] = occurrences
    
    report = {
        'date': '2026-11-18',
        'scope': 'memory/ops/*.md file-path references',
        'total_unique_refs': len(all_refs),
        'existing': len(existing),
        'phantom': len(phantom),
        'phantom_detail': {k: [(f, l) for f, l in v[:3]] for k, v in sorted(phantom.items())},
    }
    
    out_path = 'memory/archivist/doc-file-refs-report.json'
    os.makedirs('memory/archivist', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if '--json' in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"Doc file-ref consistency check (2026-11-18)")
        print(f"  Scope: memory/ops/*.md")
        print(f"  Total unique refs: {report['total_unique_refs']}")
        print(f"  Existing:          {report['existing']}")
        print(f"  Phantom:           {report['phantom']}")
        print(f"  Report: {out_path}")

if __name__ == '__main__':
    main()
