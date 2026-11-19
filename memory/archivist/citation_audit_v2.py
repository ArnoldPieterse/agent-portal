#!/usr/bin/env python3
"""Citation audit v2 (offline classifier) - Builder assist for Archivist goal #2.

v1 (citation-audit-cycle5-report.md) live-checked every URL and reported 61.2% accuracy.
Problem: it conflated (a) malformed INTERNAL portal URLs missing a slash after the port,
(b) template/placeholder tokens, and (c) bare empty schemes -- all of which are NOT broken
external citations -- with genuinely dead external domains. That depressed the accuracy figure.

This script re-classifies every URL offline (no network), then inherits v1's per-URL live
status for EXTERNAL citations only, so we can report a TRUE dead-external-citation rate and
surface the fixable internal doc bugs separately.
"""
import re, os, json, datetime, glob

MD_GLOB = "memory/**/*.md"
V1_REPORT = "memory/archivist/citation-audit-cycle5-report.md"
URL_RE  = re.compile(r'https?://[^\s\)>\]"\']+', re.I)
INTERNAL_HOSTS = {"white","black","red","blue","pale"}

def is_template(u):
    low = u.lower()
    if any(t in low for t in ("{", "}", "<", ">")):
        return True
    # port glued to path with no slash (host:portapi) and not a real external domain
    hostpart = low.split("//")[-1].split("/")[0]
    if re.match(r'^[a-z]{2,15}:\d{2,5}api', hostpart, re.I):
        return True
    return False

def classify(u):
    low = u.lower().rstrip('.,;:)]}')
    m = re.match(r'https?://([^/]+)', low)
    netloc = m.group(1) if m else ""
    host = netloc.split('@')[-1].split(':')[0]
    if not host or host == "":
        return "BARE-EMPTY", "bare scheme, no host (placeholder)"
    if is_template(u):
        mm = re.match(r'([a-z]{2,15}):(\d{2,5})api', low.split('//')[-1], re.I)
        if mm and host in INTERNAL_HOSTS:
            return "INTERNAL-MALFORMED", f"missing slash after port -> {mm.group(1)}:{mm.group(2)}/api"
        return "TEMPLATE", "placeholder/template token, not a real citation"
    if host in INTERNAL_HOSTS or host == "localhost":
        return "INTERNAL-OK", f"internal portal endpoint ({host})"
    return "EXTERNAL", ""

def host_of(u):
    m = re.match(r'https?://([^/]+)', u.lower().rstrip('.,;:)]}'))
    if not m: return ""
    h = m.group(1).split('@')[-1].split(':')[0]
    return h

def load_v1_status():
    """Map host -> (status, detail) from the v1 per-URL table. Skip bare/template rows."""
    status = {}
    try:
        txt = open(V1_REPORT, encoding="utf-8", errors="replace").read()
    except Exception:
        return status
    for line in txt.splitlines():
        if not line.startswith("|"): continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        # | # | URL | Status | Detail | Source File(s) |
        if len(cells) >= 4 and re.match(r'^\d+$', cells[0]):
            url = cells[1].rstrip('.,;:)]}')
            h = host_of(url)
            if not h or h in ("{host}", "host") :   # skip bare/empty/template v1 rows
                continue
            status.setdefault(h, []).append((cells[2], cells[3]))
    return status

def main():
    v1 = load_v1_status()
    urls = {}
    _excl = {"citation-audit-cycle5-v2-report.md","citation-audit-cycle5-v2.json"}
    for f in glob.glob(MD_GLOB, recursive=True):
        if os.path.basename(f) in _excl:
            continue
        try: txt = open(f, encoding="utf-8", errors="replace").read()
        except Exception: continue
        rel = f.replace(os.sep, "/")
        for m in URL_RE.findall(txt):
            u = m.rstrip('.,;:)]}')
            urls.setdefault(u, set()).add(rel)

    rows, cat_count = [], {}
    for u, files in sorted(urls.items()):
        cat, detail = classify(u)
        status = "n/a"
        if cat == "EXTERNAL":
            # inherit v1 live result by matching on host (v1 already live-checked these)
            h = host_of(u)
            cands = v1.get(h, [])
            matched = cands[0] if cands else None
            status = matched[0] if matched else "NOT-RECHECKED"
            detail = (detail + (" | " + matched[1] if matched else " (not in v1 sample; live-check on a net seat)")).strip(" |")
        subcat = status if cat == "EXTERNAL" else cat
        cat_count[subcat] = cat_count.get(subcat, 0) + 1
        rows.append({"url": u, "category": cat, "status": status, "detail": detail, "files": sorted(files)})

    total = len(rows)
    external = [r for r in rows if r["category"] == "EXTERNAL"]
    ext_pass = sum(1 for r in external if r["status"] == "PASS")
    ext_dead = sum(1 for r in external if r["status"].startswith("FAIL"))
    ext_warn = sum(1 for r in external if r["status"] == "WARN")
    true_dead_rate = (ext_dead / len(external) * 100) if external else 0.0

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meaning = {
        "PASS":"external citation live",
        "WARN":"external reachable but restricted/non-2xx",
        "FAIL":"external domain dead/unreachable (real broken citation)",
        "NOT-RECHECKED":"external, no v1 row matched",
        "INTERNAL-MALFORMED":"internal portal URL missing slash after port - FIXABLE DOC BUG",
        "TEMPLATE":"placeholder/template token, not a real citation",
        "BARE-EMPTY":"bare scheme with no host (placeholder)",
        "INTERNAL-OK":"well-formed internal endpoint",
    }
    out = ["# Citation Accuracy Audit v2 - Cycle 5 (Builder assist, Archivist goal #2)",
           "", f"Generated: {now}",
           "Method: offline URL classification over memory/**/*.md. EXTERNAL citations inherit",
           "v1's live status; INTERNAL/TEMPLATE/BARE are separated out because they are NOT",
           "broken external citations (v1 miscounted them as dead).", "",
           "## Classification summary", "| Category | Count | Meaning |", "|---|---|---|"]
    for k in ["PASS","WARN","FAIL","NOT-RECHECKED","INTERNAL-MALFORMED","TEMPLATE","BARE-EMPTY","INTERNAL-OK"]:
        if cat_count.get(k):
            out.append(f"| {k} | {cat_count[k]} | {meaning.get(k,'')} |")
    out += ["", "## Key finding (vs v1)",
        f"- Total unique URLs: **{total}**",
        f"- Genuinely external citations: **{len(external)}** (PASS {ext_pass}, WARN {ext_warn}, dead {ext_dead})",
        f"- **True dead-external-citation rate: {true_dead_rate:.1f}%**  (goal target >90% accuracy = <10% dead)",
        f"- Malformed internal URLs (fixable doc bugs v1 miscounted as dead): **{cat_count.get('INTERNAL-MALFORMED',0)}**",
        f"- Placeholders/templates/bare (not real citations): **{cat_count.get('TEMPLATE',0)+cat_count.get('BARE-EMPTY',0)}**",
        "", "## Fixable malformed internal URLs (missing slash after port)",
        "| URL | Suggested fix | File(s) |"]
    for r in rows:
        if r["category"] == "INTERNAL-MALFORMED":
            fixed = re.sub(r'([a-z]{2,15}):(\d{2,5})api', r'\1:\2/api', r["url"], count=1, flags=re.I)
            out.append(f"| `{r['url']}` | `{fixed}` | {', '.join(r['files'])} |")
    out += ["", "## All URLs (classified)", "| URL | Category | Status | Detail | File(s) |"]
    for r in rows:
        out.append(f"| `{r['url'][:80]}` | {r['category']} | {r['status']} | {r['detail'][:60]} | {', '.join(r['files'])[:70]} |")

    open("memory/archivist/citation-audit-cycle5-v2-report.md","w",encoding="utf-8").write("\n".join(out)+"\n")
    json.dump({"generated": now, "total": total, "external": len(external),
               "ext_pass": ext_pass, "ext_warn": ext_warn, "ext_dead": ext_dead,
               "true_dead_rate_pct": round(true_dead_rate,1), "cat_count": cat_count, "rows": rows},
              open("memory/archivist/citation-audit-cycle5-v2.json","w",encoding="utf-8"), indent=2)

    print(f"total={total} external={len(external)} pass={ext_pass} warn={ext_warn} dead={ext_dead}")
    print(f"true_dead_rate={true_dead_rate:.1f}%  malformed_internal={cat_count.get('INTERNAL-MALFORMED',0)}")
    print("cat_count=", cat_count)

if __name__ == "__main__":
    main()
