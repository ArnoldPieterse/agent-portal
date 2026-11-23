#!/usr/bin/env python3
"""provenance_ledger.py - Archivist Goal 1 (cycle-12): Fact-Level Provenance Ledger.

For every fact (heading) in knowledge-index.json, records the full chain:
  {fact_id -> source_file:line -> extraction_rule -> confidence -> last_verified}

Emits memory/archivist/provenance-ledger.json so the Cockpit can answer
"where did this number come from" on click.

Usage:
  python memory/archivist/provenance_ledger.py              # build + verify
  python memory/archivist/provenance_ledger.py --verify     # spot-check only
  python memory/archivist/provenance_ledger.py --stale-check  # re-verify all, flag stale
"""
import json, pathlib, hashlib, re, os, sys, random
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def fact_id(path, kind, value, line):
    """Deterministic ID for a fact."""
    raw = path + "|" + kind + "|" + value + "|" + str(line)
    return hashlib.sha1(raw.encode()).hexdigest()[:12]

def find_heading_lines(filepath, headings):
    """Find line numbers for each heading in the source file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except (OSError, IOError):
        return None
    
    result = {}
    for heading in headings:
        h_norm = heading.strip().lower().lstrip('#').strip()
        found = False
        for i, line in enumerate(lines, 1):
            l_norm = line.strip().lower().lstrip('#').strip()
            if l_norm == h_norm or (len(h_norm) > 5 and h_norm in l_norm):
                result[heading] = i
                found = True
                break
        if not found:
            result[heading] = None
    return result

def build_ledger(ki_path='memory/archivist/knowledge-index.json', out_path='memory/archivist/provenance-ledger.json'):
    ki = json.loads(pathlib.Path(ki_path).read_text(encoding='utf-8'))
    docs = ki['docs']
    timestamp = now_iso()
    
    ledger = {
        'generated': timestamp,
        'source_index': ki_path,
        'doc_count': len(docs),
        'fact_count': 0,
        'facts_with_provenance': 0,
        'facts': []
    }
    
    for doc in docs:
        path = doc['path']
        headings = doc.get('headings', [])
        
        src_exists = pathlib.Path(path).exists()
        heading_lines = None
        if src_exists and headings:
            heading_lines = find_heading_lines(path, headings)
        
        for h in headings:
            fid = fact_id(path, 'heading', h, heading_lines.get(h) if heading_lines else 0)
            line = heading_lines.get(h) if heading_lines else None
            
            if line is not None:
                confidence = 0.95
            elif src_exists:
                confidence = 0.6
            else:
                confidence = 0.2
            
            fact_entry = {
                'fact_id': fid,
                'source_file': path,
                'line': line,
                'extraction_rule': 'heading_parse',
                'value': h,
                'confidence': confidence,
                'last_verified': timestamp if line is not None else None,
                'status': 'verified' if line is not None else ('stale' if src_exists else 'missing_source')
            }
            ledger['facts'].append(fact_entry)
            ledger['fact_count'] += 1
            if line is not None:
                ledger['facts_with_provenance'] += 1
    
    pathlib.Path(out_path).write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    
    print("Provenance ledger built: " + out_path)
    print("  Total facts: %d" % ledger['fact_count'])
    print("  Facts with resolvable provenance (line found): %d" % ledger['facts_with_provenance'])
    pct = ledger['facts_with_provenance'] / max(1, ledger['fact_count']) * 100
    print("  Coverage: %.1f%%" % pct)
    
    return ledger

def verify_ledger(ledger_path='memory/archivist/provenance-ledger.json', n_checks=10):
    """Spot-check N random facts against source files."""
    ledger = json.loads(pathlib.Path(ledger_path).read_text(encoding='utf-8'))
    verified_facts = [f for f in ledger['facts'] if f['status'] == 'verified' and f['line'] is not None]
    
    if len(verified_facts) < n_checks:
        sample = verified_facts
    else:
        sample = random.sample(verified_facts, n_checks)
    
    print("")
    print("Spot-checking %d facts against source:" % len(sample))
    passed = 0
    failed = 0
    for f in sample:
        try:
            with open(f['source_file'], 'r', encoding='utf-8', errors='replace') as src:
                lines = src.readlines()
            line_idx = f['line'] - 1
            if 0 <= line_idx < len(lines):
                actual = lines[line_idx].strip().lower().lstrip('#').strip()
                expected = f['value'].strip().lower().lstrip('#').strip()
                match = (actual == expected) or (len(expected) > 5 and expected in actual)
                if match:
                    passed += 1
                    print("  PASS: %s:%d" % (f['source_file'], f['line']))
                else:
                    failed += 1
                    print("  FAIL: %s:%d expected [%s] got [%s]" % (f['source_file'], f['line'], expected[:40], actual[:40]))
            else:
                failed += 1
                print("  FAIL: %s:%d out of range" % (f['source_file'], f['line']))
        except (OSError, IOError) as e:
            failed += 1
            print("  FAIL: %s -> %s" % (f['source_file'], str(e)))
    
    print("")
    print("Spot-check result: %d/%d passed" % (passed, len(sample)))
    return passed == len(sample)

def stale_check(ledger_path='memory/archivist/provenance-ledger.json'):
    """Re-verify all facts; flag any whose source line no longer matches."""
    ledger = json.loads(pathlib.Path(ledger_path).read_text(encoding='utf-8'))
    timestamp = now_iso()
    
    stale_count = 0
    still_ok = 0
    
    for f in ledger['facts']:
        if f['status'] != 'verified' or f['line'] is None:
            continue
        try:
            with open(f['source_file'], 'r', encoding='utf-8', errors='replace') as src:
                lines = src.readlines()
            line_idx = f['line'] - 1
            if 0 <= line_idx < len(lines):
                actual = lines[line_idx].strip().lower().lstrip('#').strip()
                expected = f['value'].strip().lower().lstrip('#').strip()
                match = (actual == expected) or (len(expected) > 5 and expected in actual)
                if match:
                    still_ok += 1
                else:
                    stale_count += 1
                    f['status'] = 'stale'
                    f['stale_detected'] = timestamp
            else:
                stale_count += 1
                f['status'] = 'stale'
                f['stale_detected'] = timestamp
        except (OSError, IOError):
            stale_count += 1
            f['status'] = 'missing_source'
    
    ledger['last_stale_check'] = timestamp
    ledger['stale_count'] = stale_count
    
    pathlib.Path(ledger_path).write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    print("Stale check complete: %d still OK, %d flagged stale" % (still_ok, stale_count))
    return stale_count

if __name__ == '__main__':
    if '--verify' in sys.argv:
        ok = verify_ledger()
        sys.exit(0 if ok else 1)
    elif '--stale-check' in sys.argv:
        stale_check()
    else:
        ledger = build_ledger()
        print("")
        print("--- Auto spot-check ---")
        ok = verify_ledger()
        print("")
        print("Verification: " + ("PASS" if ok else "FAIL"))
