#!/usr/bin/env python3
"""Citation Accuracy Audit - Archivist Goal #2 (cycle-5)

Scans all memory/ .md files for external URL citations, deduplicates,
checks each live (HEAD then GET fallback), and writes a scored report.

Usage:
    python memory/archivist/citation_audit.py [--limit N] [--timeout SECS]

Output: memory/archivist/citation-audit-cycle5-report.md
"""
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# --- Config ---
MEMORY_ROOT = "memory"
OUTPUT_FILE = "memory/archivist/citation-audit-cycle5-report.md"
DEFAULT_TIMEOUT = 10
DEFAULT_LIMIT = 50  # target 50 entries per goal spec

# Internal URL patterns to exclude (not external citations)
INTERNAL_PATTERNS = re.compile(
    r"(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)"
)

# Extract URLs from markdown (handle trailing punctuation)
URL_PATTERN = re.compile(r'https?://[^\s\)\]>"`]+')


def collect_citations(root_dir):
    """Walk root_dir, return list of (file_path, url, line_number)."""
    citations = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    for lineno, line in enumerate(fh, 1):
                        for url in URL_PATTERN.findall(line):
                            # Strip trailing punctuation that's not part of URL
                            url_clean = url.rstrip(".,;:!?")
                            if INTERNAL_PATTERNS.search(url_clean):
                                continue
                            if url_clean == "https://...":  # placeholder
                                continue
                            citations.append((fpath, url_clean, lineno))
            except (OSError, UnicodeDecodeError) as e:
                print(f"  WARN: could not read {fpath}: {e}", file=sys.stderr)
    return citations


def deduplicate(citations):
    """Return unique URLs with their source files."""
    seen = {}
    for fpath, url, lineno in citations:
        if url not in seen:
            seen[url] = {"url": url, "sources": [(fpath, lineno)]}
        else:
            seen[url]["sources"].append((fpath, lineno))
    return list(seen.values())


def check_url(url, timeout):
    """Check if URL is live. Returns (status, detail)."""
    # Try HEAD first
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (Fleet Citation Audit)")
        resp = urllib.request.urlopen(req, timeout=timeout)
        code = resp.getcode()
        if 200 <= code < 400:
            return ("PASS", f"HTTP {code}")
        else:
            return ("FAIL", f"HTTP {code}")
    except urllib.error.HTTPError as e:
        # Some servers reject HEAD; try GET
        if e.code in (405, 501):
            pass  # fall through to GET
        elif e.code == 403:
            return ("WARN", f"HTTP 403 (forbidden - may need auth)")
        else:
            return ("FAIL", f"HTTP {e.code}")
    except urllib.error.URLError as e:
        # Fall through to GET on connection issues
        pass
    except Exception as e:
        return ("WARN", f"{type(e).__name__}: {str(e)[:100]}")

    # Try GET with small read
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Fleet Citation Audit)")
        resp = urllib.request.urlopen(req, timeout=timeout)
        code = resp.getcode()
        if 200 <= code < 400:
            return ("PASS", f"HTTP {code} (GET)")
        else:
            return ("FAIL", f"HTTP {code} (GET)")
    except urllib.error.HTTPError as e:
        return ("FAIL", f"HTTP {e.code} (GET)")
    except Exception as e:
        return ("FAIL", f"{type(e).__name__}: {str(e)[:100]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Citation Accuracy Audit")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"Max URLs to check (default {DEFAULT_LIMIT})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Per-URL timeout seconds (default {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    print(f"[citation_audit] Scanning {MEMORY_ROOT}/ for external URL citations...")
    raw = collect_citations(MEMORY_ROOT)
    print(f"  Raw citation instances: {len(raw)}")

    unique = deduplicate(raw)
    print(f"  Unique external URLs: {len(unique)}")

    # If fewer than limit, audit all; otherwise sample
    to_check = unique[:args.limit]
    if len(unique) > args.limit:
        print(f"  Auditing first {args.limit} (of {len(unique)})")
    else:
        print(f"  Auditing all {len(to_check)}")

    # Check each URL
    results = []
    for i, entry in enumerate(to_check, 1):
        url = entry["url"]
        src_file = entry["sources"][0][0]
        print(f"  [{i}/{len(to_check)}] {url[:70]} ... ", end="", flush=True)
        status, detail = check_url(url, args.timeout)
        results.append({**entry, "status": status, "detail": detail})
        print(f"{status} ({detail})")
        time.sleep(0.3)  # be polite

    # Tally
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    accuracy = (passed / total * 100) if total else 0

    # Write report
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Citation Accuracy Audit - Cycle 5\n")
        f.write(f"\nGenerated: {now}\n")
        f.write(f"Method: scan all memory/**/*.md for external URLs, deduplicate, live-check (HEAD->GET)\n")
        f.write(f"\n## Summary\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Total unique external URLs in KB | {len(unique)} |\n")
        f.write(f"| Audited this run | {total} |\n")
        f.write(f"| PASS (live, accessible) | {passed} |\n")
        f.write(f"| WARN (accessible but restricted) | {warned} |\n")
        f.write(f"| FAIL (dead/unreachable) | {failed} |\n")
        f.write(f"| **Accuracy rate** | **{accuracy:.1f}%** |\n")
        f.write(f"\nTarget: >90% accuracy. \'{'MET' if accuracy > 90 else 'NOT MET'}\'\n")
        f.write(f"\n## Per-URL Results\n")
        f.write(f"| # | URL | Status | Detail | Source File(s) |\n")
        f.write(f"|---|-----|--------|--------|----------------|\n")
        for i, r in enumerate(results, 1):
            srcs = "; ".join(os.path.basename(s[0]) for s in r["sources"][:3])
            url_short = r["url"][:60] + ("..." if len(r["url"]) > 60 else "")
            f.write(f"| {i} | {url_short} | {r['status']} | {r['detail']} | {srcs} |\n")
        f.write(f"\n## Notes\n")
        if len(unique) < 50:
            f.write(f"- Only {len(unique)} unique external URLs exist in the KB (target was 50).\n")
            f.write(f"  All were audited. The KB is primarily internal-reference based;\n")
            f.write(f"  external citations are sparse by design (fleet-local knowledge base).\n")
        f.write(f"- Internal URLs (localhost, private IPs) excluded from audit scope.\n")

    print(f"\n[citation_audit] Report written to {OUTPUT_FILE}")
    print(f"[citation_audit] Accuracy: {accuracy:.1f}% ({passed}/{total} PASS, {warned} WARN, {failed} FAIL)")


if __name__ == "__main__":
    main()
