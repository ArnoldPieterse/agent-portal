"""
Source Reliability Scorer
=========================
Usage: python memory/researcher/source_scorer.py <url>
Returns a 0-100 reliability score based on:
  - domain authority (tiered)
  - citation count in local KB files
  - recency signals (date in URL or KB references)
  - consistency with existing KB entries

Exit code: 0 = scored, 1 = bad input.
"""
import sys, os, re, json, datetime
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Domain authority tiers (base score out of 40)
# ---------------------------------------------------------------------------
AUTHORITY_TIERS = {
    # Tier 5 - government / standards bodies (36-40)
    '.gov': 38, '.mil': 38,
    'nist.gov': 39, 'whitehouse.gov': 40, 'fda.gov': 39, 'cdc.gov': 38,
    'iso.org': 37, 'w3.org': 37, 'ietf.org': 38, 'rfc-editor.org': 38,

    # Tier 4 - academic journals / preprint servers (30-35)
    'nature.com': 35, 'science.org': 35, 'cell.com': 34,
    'arxiv.org': 32, 'semanticscholar.org': 31, 'acm.org': 34,
    'ieee.org': 34, 'springer.com': 32, 'wiley.com': 31,
    'mdpi.com': 28, 'mdpi-res.com': 28,

    # Tier 3 - established reference / encyclopedic (20-29)
    'wikipedia.org': 24, 'britannica.com': 28, 'merriam-webster.com': 26,
    'docs.python.org': 30, 'developer.mozilla.org': 29, 'kubernetes.io': 30,
    'go.dev': 30, 'rust-lang.org': 29, 'nodejs.org': 28,

    # Tier 2 - major news / tech media (10-19)
    'reuters.com': 18, 'apnews.com': 17, 'bloomberg.com': 16,
    'theverge.com': 15, 'wired.com': 14, 'arstechnica.com': 15,
    'hackernoon.com': 10, 'medium.com': 8,

    # Tier 1 - forums / social / blogs (0-9)
    'reddit.com': 3, 'news.ycombinator.com': 6, 'stackoverflow.com': 12,
    'twitter.com': 2, 'x.com': 2, 'facebook.com': 2, 'pinterest.com': 1,
    'blogspot.com': 3, 'wordpress.com': 4, 'tumblr.com': 2,
}

# Fallback: .edu domains get a floor of 26
EDU_FLOOR = 26

# ---------------------------------------------------------------------------
# Citation count (0-25): grep local KB/memory files for the domain
# ---------------------------------------------------------------------------
def count_citations(domain: str, search_root: str) -> int:
    """Count how many times this domain appears in .md/.json files under search_root."""
    count = 0
    for dirpath, _, filenames in os.walk(search_root):
        # Skip huge dirs
        if any(skip in dirpath.lower() for skip in ['node_modules', '.git', '__pycache__']):
            continue
        for fn in filenames:
            if not fn.endswith(('.md', '.json', '.txt')):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                count += text.lower().count(domain.lower())
            except Exception:
                pass
    return count

def citation_score(count: int) -> float:
    """Map raw count to 0-25 scale (log-ish)."""
    if count == 0:   return 3.0   # no local citations - not disqualifying, just neutral-low
    if count <= 1:   return 8.0
    if count <= 3:   return 14.0
    if count <= 10:  return 20.0
    if count <= 50:  return 24.0
    return 25.0

# ---------------------------------------------------------------------------
# Recency (0-15): date patterns in URL or KB entries
# ---------------------------------------------------------------------------
def recency_score(url: str, now: datetime.date) -> float:
    """Score 0-15 based on whether the URL or its references look recent."""
    url_lower = url.lower()

    # Look for YYYY-MM-DD or YYYY/MM/DD in the URL path
    m = re.search(r'(20\d{2})[-/](\d{1,2})(?:[-/](\d{1,2}))?', url_lower)
    if m:
        year = int(m.group(1))
        try:
            d = datetime.date(year, int(m.group(2)), 1)
            age_days = (now - d).days
            if age_days <= 30:    return 15.0
            if age_days <= 90:    return 12.0
            if age_days <= 365:   return 8.0
            if age_days <= 730:   return 4.0
            return 1.0
        except ValueError:
            pass

    # No date in URL - neutral (moderate score, since many authoritative sources have no dates)
    return 7.0

# ---------------------------------------------------------------------------
# Consistency with KB (0-20): does the domain appear alongside known terms?
# ---------------------------------------------------------------------------
def consistency_score(domain: str, kb_files: list) -> float:
    """
    Score 0-20 based on whether the domain's content is consistent with
    existing KB entries. Heuristic: if the domain is cited in files that also
    contain dictionary terms, it likely aligns with our knowledge base.
    """
    all_terms = set()
    for kf in kb_files:
        if os.path.exists(kf):
            try:
                with open(kf) as f:
                    data = json.load(f)
                for k in data:
                    if not k.startswith('_'):
                        all_terms.add(k.lower())
            except Exception:
                pass

    if not all_terms:
        return 10.0  # neutral - no KB to check against

    term_hits = 0
    total_files_checked = 0
    for dirpath, _, filenames in os.walk('memory'):
        for fn in filenames:
            if not fn.endswith(('.md', '.json', '.txt')):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().lower()
            except Exception:
                continue
            if domain.lower() in text:
                total_files_checked += 1
                for term in all_terms:
                    if term in text:
                        term_hits += 1
                        break  # one hit per file is enough

    if total_files_checked == 0:
        return 8.0   # domain not found in any local file - neutral-low
    ratio = min(term_hits / total_files_checked, 1.0)
    return round(5.0 + ratio * 15.0, 1)  # range: 5-20

# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------
def score_url(url: str, search_root: str = 'memory', now: datetime.date = None) -> dict:
    if now is None:
        now = datetime.date.today()

    parsed = urlparse(url)
    host = (parsed.netloc or '').lower().removeprefix('www.')
    if not host:
        return {'url': url, 'error': 'no host in URL', 'total': 0}

    # --- Authority (0-40) ---
    auth_score = None
    for pattern, sc in AUTHORITY_TIERS.items():
        if pattern.startswith('.') and host.endswith(pattern):
            auth_score = max(auth_score or 0, sc)
        elif pattern in host:
            auth_score = max(auth_score or 0, sc)
    if auth_score is None:
        # Check .edu
        if host.endswith('.edu'):
            auth_score = EDU_FLOOR
        else:
            # Unknown domain - base score of 8 (could be a personal blog or unknown site)
            auth_score = 8.0
    auth_score = float(auth_score)

    # --- Citations (0-25) ---
    raw_citations = count_citations(host, search_root)
    cit_score = citation_score(raw_citations)

    # --- Recency (0-15) ---
    rec_score = recency_score(url, now)

    # --- Consistency (0-20) ---
    kb_files = [
        os.path.join(search_root, 'researcher', 'dictionary_core.json'),
        os.path.join(search_root, 'researcher', 'dictionary_project.json'),
    ]
    cons_score = consistency_score(host, kb_files)

    total = round(auth_score + cit_score + rec_score + cons_score, 1)
    total = max(0.0, min(100.0, total))

    return {
        'url': url,
        'domain': host,
        'authority': round(auth_score, 1),
        'citations_raw': raw_citations,
        'citations_score': round(cit_score, 1),
        'recency': round(rec_score, 1),
        'consistency': round(cons_score, 1),
        'total': total,
    }

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/researcher/source_scorer.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    result = score_url(url)

    if 'error' in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    # Pretty print
    print(f"URL:          {result['url']}")
    print(f"Domain:       {result['domain']}")
    print(f"Authority:    {result['authority']:5.1f} / 40")
    print(f"Citations:    {result['citations_raw']:>3d} raw  ->  {result['citations_score']:4.1f} / 25")
    print(f"Recency:      {result['recency']:5.1f} / 15")
    print(f"Consistency:  {result['consistency']:5.1f} / 20")
    print("-" * 40)
    print(f"TOTAL:        {result['total']:5.1f} / 100")

if __name__ == '__main__':
    main()
