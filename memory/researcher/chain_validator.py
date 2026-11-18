#!/usr/bin/env python3
"""
Evidence Chain Validator - Researcher Goal #7 (cycle-5)

Usage:
    python memory/researcher/chain_validator.py <evidence_file.md>

Checks:
  1. Every claim has >= 2 independent sources (different domains)
  2. No circular references (source pointing to the file itself)
  3. Timestamps in the file are monotonic (non-decreasing top-to-bottom)

Exit codes:
  0 = PASS (all checks green)
  1 = FAIL (one or more checks failed, details printed)
  2 = Usage error / file not found
"""
import sys
import re
import os
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path


def parse_claims(text: str) -> list[dict]:
    """Extract claims and their associated source URLs from markdown.
    
    A claim is identified by:
      - '## Claim' header (followed by a quoted line or plain text until next '##')
      - '- **Claim**:' inline marker
    
    Sources are URLs (http/https) found in the section belonging to that claim.
    """
    claims = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Pattern 1: '## Claim' header
        if re.match(r'^##\s+Claim\b', line, re.IGNORECASE):
            claim_text_parts = []
            source_urls = []
            # Collect until next '## ' header (any, including another Claim) or EOF
            j = i + 1
            while j < len(lines) and not re.match(r'^##\s+', lines[j]):
                l = lines[j]
                # Capture the claim statement (quoted line after header)
                m_quote = re.match(r'^>\s*(.+)', l)
                if m_quote and not claim_text_parts:
                    claim_text_parts.append(m_quote.group(1).strip())
                elif l.strip() and not l.startswith('#') and not l.startswith('##'):
                    # Capture non-header text as part of claim description
                    if not any(u in l for u in ('http://', 'https://')):
                        claim_text_parts.append(l.strip())
                # Collect URLs
                urls = re.findall(r'https?://[^\s)\]>"\'`]+', l)
                source_urls.extend(urls)
                j += 1
            claims.append({
                'text': ' '.join(claim_text_parts)[:200],
                'sources': list(set(source_urls)),
                'line_start': i + 1,
                'line_end': j,
            })
            i = j
        # Pattern 2: inline '- **Claim**:' or '**Claim**:'
        elif re.match(r'^\s*[-*]?\s*\*\*Claim\*\*:', line):
            claim_text_parts = []
            source_urls = []
            m = re.match(r'^\s*[-*]?\s*\*\*Claim\*\*:\s*(.+)', line)
            if m:
                claim_text_parts.append(m.group(1).strip())
            j = i + 1
            while j < len(lines) and not re.match(r'^##\s', lines[j]) and \
                  not re.match(r'^\s*[-*]?\s*\*\*Claim\*\*:', lines[j]):
                l = lines[j]
                urls = re.findall(r'https?://[^\s)\]>"\'`]+', l)
                source_urls.extend(urls)
                j += 1
            claims.append({
                'text': ' '.join(claim_text_parts)[:200],
                'sources': list(set(source_urls)),
                'line_start': i + 1,
                'line_end': j,
            })
            i = j
        else:
            i += 1
    return claims


def get_domain(url: str) -> str:
    """Extract domain from URL (lowercase, no port)."""
    try:
        p = urlparse(url)
        host = (p.netloc or '').lower().split(':')[0]
        # Strip leading 'www.'
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def check_independent_sources(claim: dict, min_sources: int = 2) -> list[str]:
    """Return list of issues if claim has fewer than min_sources from independent domains."""
    issues = []
    domains = set()
    for url in claim['sources']:
        d = get_domain(url)
        if d:
            domains.add(d)
    if len(domains) < min_sources:
        issues.append(
            f"Claim '{claim['text'][:60]}...' has {len(domains)} unique domain(s); need >= {min_sources}"
        )
    return issues


def check_circular_references(claims: list[dict], file_path: str) -> list[str]:
    """Check that no source URL points to the evidence file itself."""
    issues = []
    fname = os.path.basename(file_path).lower()
    for claim in claims:
        for url in claim['sources']:
            if fname in url.lower():
                issues.append(
                    f"Circular reference: source {url} points to the evidence file itself"
                )
    # Also check: no two claims share ALL their source domains (indicates copy-paste)
    if len(claims) >= 2:
        for a in range(len(claims)):
            for b in range(a + 1, len(claims)):
                da = {get_domain(u) for u in claims[a]['sources']}
                db = {get_domain(u) for u in claims[b]['sources']}
                if da and da == db:
                    issues.append(
                        f"Claims at lines {claims[a]['line_start']} and {claims[b]['line_start']} "
                        f"share identical source domain set {da} - possible circular dependency"
                    )
    return issues


TS_PATTERNS = [
    (re.compile(r'^Date:\s*(\d{4}-\d{2}-\d{2})'), 'date_field'),
    (re.compile(r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})'), 'iso_ts'),
]


def check_monotonic_timestamps(text: str) -> list[str]:
    """Extract all timestamps and verify they are non-decreasing top-to-bottom."""
    issues = []
    found_ts = []  # (line_num, datetime)
    for line_no, line in enumerate(text.split('\n'), 1):
        for pat, kind in TS_PATTERNS:
            m = pat.search(line)
            if m:
                try:
                    ts_str = m.group(1)
                    if 'T' in ts_str:
                        dt = datetime.fromisoformat(ts_str)
                    else:
                        dt = datetime.strptime(ts_str, '%Y-%m-%d')
                    found_ts.append((line_no, dt))
                except ValueError:
                    pass
    for i in range(1, len(found_ts)):
        if found_ts[i][1] < found_ts[i-1][1]:
            issues.append(
                f"Non-monotonic timestamp: line {found_ts[i][0]} ({found_ts[i][1].isoformat()}) "
                f"is earlier than line {found_ts[i-1][0]} ({found_ts[i-1][1].isoformat()})"
            )
    return issues


def validate(evidence_file: str) -> dict:
    """Run all checks on an evidence file. Returns {'pass': bool, 'issues': [...], 'stats': {...}}."""
    if not os.path.isfile(evidence_file):
        return {'pass': False, 'issues': [f'File not found: {evidence_file}'], 'stats': {}}
    
    with open(evidence_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    all_issues = []
    claims = parse_claims(text)
    
    if not claims:
        all_issues.append("No identifiable claims found (expected '## Claim' header or '- **Claim**:' pattern)")
    else:
        # Check 1: independent sources per claim
        for claim in claims:
            all_issues.extend(check_independent_sources(claim))
        
        # Check 2: circular references
        all_issues.extend(check_circular_references(claims, evidence_file))
    
    # Check 3: monotonic timestamps
    all_issues.extend(check_monotonic_timestamps(text))
    
    stats = {
        'file': evidence_file,
        'total_claims': len(claims),
        'claims_with_2plus_sources': sum(
            1 for c in claims if len({get_domain(u) for u in c['sources']}) >= 2
        ),
    }
    return {'pass': len(all_issues) == 0, 'issues': all_issues, 'stats': stats}


def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/researcher/chain_validator.py <evidence_file.md> [more_files...]")
        sys.exit(2)
    
    all_pass = True
    for filepath in sys.argv[1:]:
        result = validate(filepath)
        status = 'PASS' if result['pass'] else 'FAIL'
        print(f"\n{'='*60}")
        print(f"{status}: {filepath}")
        print(f"  Claims found: {result['stats'].get('total_claims', 0)}")
        print(f"  Claims with >=2 independent sources: {result['stats'].get('claims_with_2plus_sources', 0)}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  ISSUE: {issue}")
        else:
            print(f"  All checks passed.")
        if not result['pass']:
            all_pass = False
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()