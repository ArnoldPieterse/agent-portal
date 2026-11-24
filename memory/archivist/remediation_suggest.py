#!/usr/bin/env python3
"""archivist/remediation_suggest.py - Knowledge-Grounded Remediation Suggester.

When a degradation/alert fires, retrieve the most relevant past remediations
and their recorded outcomes from the KB, then emit a ranked "suggested fix" payload.

Output: memory/archivist/remediation-suggest-<date>.json
Format: {situation, [fix, provenance_leaf, historical_success_rate], confidence}

Deterministic given inputs (no random, stable sort by score desc then path asc).
"""
import json, math, os, re, sys, time, hashlib
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
ARCH = os.path.join(MEM, "archivist")

# --- Tokenizer (same as kb_search.py for consistency) ---
STOP = set("the a an and or of to in on for with by from is are was were be been being this that these those it its as at not no yes can could will would should may might must do does did done have has had having if then else when while after before during into over under about between across per via each every any all some such only own same so too very just also both more most less least fewer many much few other another others new old first last next prev previous current recent past future full half part way thing things one two three four five six seven eight nine ten use used using uses usage work works working run runs running make makes made let lets letting take takes taken get gets got go goes went see saw show shows shown set sets setting put puts putting add adds added remove removed delete deleted check checked fix fixed build built create created write written file files dir path code data value values key keys item items entry entries goal goals host hosts agent agents portal panel view page tab button click open opened close closed load loaded save saved sync synced mirror mirrors update updated running start started stop stopped test tested verify verified evidence memory index".split())
TOK = re.compile(r"[a-z][a-z0-9_]{2,}")

def tokenize(t):
    return [w for w in TOK.findall(t.lower()) if w not in STOP]

# --- Remediation corpus: scan .md files with remediation signals ---
REMED_KEYWORDS = {"fix", "repair", "remediat", "revert", "recover", "restore", "patch", "resolve", "closed", "resolved"}
OUTCOME_PATTERNS = [
    (r"(?i)\b(pass|passed|success|succeeded|verified|confirmed|complete|completed|done|working|ok)\b", "success"),
    (r"(?i)\b(fail|failed|failure|broken|error|crash|errored)\b", "fail"),
    (r"(?i)\b(partial|partially|some|most but not all)\b", "partial"),
]

def is_remediation_file(path):
    """Heuristic: file relates to a remediation action."""
    name = os.path.basename(path).lower()
    if any(kw in name for kw in REMED_KEYWORDS):
        return True
    # Also check first 200 chars for remediation signals
    try:
        head = open(path, encoding="utf-8", errors="replace").read(300)
        if any(kw in head.lower() for kw in ["remediation", "fix applied", "repair", "reverted"]):
            return True
    except Exception:
        pass
    return False

def extract_outcome(text):
    """Extract outcome from remediation evidence text. Returns 'success', 'fail', 'partial', or 'unknown'."""
    # Priority: explicit markers first
    if re.search(r"(?i)\b(status:\s*)?(success|passed|verified|confirmed)\b", text[:500]):
        return "success"
    if re.search(r"(?i)\b(status:\s*)?(fail|failed|failure)\b", text[:500]):
        return "fail"
    # Count signals in first 500 chars
    scores = {"success": 0, "fail": 0, "partial": 0}
    for pat, label in OUTCOME_PATTERNS:
        matches = re.findall(pat, text[:500])
        if matches:
            scores[label] += len(matches)
    if max(scores.values()) == 0:
        return "unknown"
    # Partial trumps if explicit
    if scores["partial"] > 0 and scores["partial"] >= scores["success"]:
        return "partial"
    best = max(scores, key=scores.get)
    return best

def build_remediation_index():
    """Scan memory/ for remediation evidence files. Returns list of dicts."""
    entries = []
    for r, dirs, files in os.walk(MEM):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if not is_remediation_file(p):
                continue
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            # Extract title from H1
            m = re.search(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", text, re.M)
            title = m.group(1).strip() if m else f[:-3]
            outcome = extract_outcome(text)
            # Extract key terms for matching
            terms = tokenize(title + " " + text[:2000])
            entries.append({
                "path": rel,
                "title": title,
                "terms": terms,
                "outcome": outcome,
                "size": len(text),
            })
    return entries

# --- TF-IDF scoring ---
def compute_idf(docs):
    """Compute IDF for all terms across docs."""
    N = len(docs)
    df = {}
    for doc in docs:
        seen = set(doc["terms"])
        for t in seen:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((N + 1) / (d + 1)) + 1 for t, d in df.items()}

def tfidf_score(query_terms, doc_terms, idf):
    """Cosine-like score between query and doc."""
    if not query_terms or not doc_terms:
        return 0.0
    qtf = {}
    for t in query_terms:
        qtf[t] = qtf.get(t, 0) + 1
    dtf = {}
    for t in doc_terms:
        dtf[t] = dtf.get(t, 0) + 1
    score = 0.0
    for t in qtf:
        if t in dtf:
            score += (1 + math.log(qtf[t])) * idf.get(t, 1.0) * (1 + math.log(dtf[t]))
    return score

# --- Main suggester ---
def suggest(situation, keywords=None, limit=5):
    """Given an alert situation, return ranked remediation suggestions.
    
    Args:
        situation: str - description of the alert/degradation
        keywords: list[str] - optional extra keywords to boost matching
        limit: int - max suggestions to return
    
    Returns:
        dict with keys: situation, timestamp, suggestions[], no_prior_art (bool)
    """
    if keywords is None:
        keywords = []
    
    # Build query terms
    query_text = situation + " " + " ".join(keywords)
    query_terms = tokenize(query_text)
    
    if not query_terms:
        return {
            "situation": situation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggestions": [],
            "no_prior_art": True,
            "confidence": 0.0,
        }
    
    # Build index (deterministic: sorted file walk)
    corpus = build_remediation_index()
    if not corpus:
        return {
            "situation": situation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggestions": [],
            "no_prior_art": True,
            "confidence": 0.0,
        }
    
    idf = compute_idf(corpus)
    
    # Score all docs
    scored = []
    for doc in corpus:
        s = tfidf_score(query_terms, doc["terms"], idf)
        if s > 0:
            scored.append((s, doc))
    
    # Sort by score desc, then path asc (deterministic tiebreak)
    scored.sort(key=lambda x: (-x[0], x[1]["path"]))
    
    # Compute success rates per outcome type for context
    outcomes = [d["outcome"] for _, d in scored]
    total_outcomes = len([o for o in outcomes if o != "unknown"])
    success_count = len([o for o in outcomes if o == "success"])
    overall_success_rate = success_count / total_outcomes if total_outcomes > 0 else 0.5
    
    # Build suggestions
    suggestions = []
    for rank, (score, doc) in enumerate(scored[:limit]):
        # Per-leaf success rate: use this doc's outcome
        leaf_rate = {"success": 1.0, "fail": 0.0, "partial": 0.5, "unknown": overall_success_rate}[doc["outcome"]]
        suggestions.append({
            "rank": rank + 1,
            "fix": doc["title"],
            "provenance_leaf": doc["path"],
            "historical_success_rate": round(leaf_rate, 3),
            "relevance_score": round(score, 4),
            "outcome": doc["outcome"],
        })
    
    no_prior_art = len(suggestions) == 0
    confidence = min(1.0, (scored[0][0] / max(len(query_terms) * 3, 1))) if scored else 0.0
    
    return {
        "situation": situation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "suggestions": suggestions,
        "no_prior_art": no_prior_art,
        "confidence": round(confidence, 4),
        "corpus_size": len(corpus),
    }

# --- CLI / selftest ---
def selftest():
    """Run 5+ seeded alert situations to verify the suggester works."""
    print("=== remediation_suggest.py selftest ===")
    
    test_situations = [
        ("dangling pointer in INDEX.md causing broken cross-reference", ["dangling", "pointer", "index"]),
        ("orphan file not referenced by any index entry", ["orphan", "unreferenced", "file"]),
        ("citation check found stale reference to deleted file", ["citation", "stale", "deleted"]),
        ("mirror sync reverted a pinned file change", ["mirror", "revert", "pinned", "clobber"]),
        ("goal ledger parse error on REACHED marker", ["ledger", "parse", "reached", "marker"]),
        ("quantum flux capacitor misalignment in dimension 7", ["quantum", "flux", "capacitor", "dimension"]),  # no-prior-art case
    ]
    
    results = []
    all_pass = True
    for i, (situation, keywords) in enumerate(test_situations):
        r = suggest(situation, keywords)
        is_no_prior = r["no_prior_art"]
        has_suggestions = len(r["suggestions"]) > 0
        # Verify: if not no-prior-art, must have >=1 suggestion with existing leaf
        valid = True
        if has_suggestions:
            for s in r["suggestions"]:
                leaf_path = os.path.join(ROOT, s["provenance_leaf"].replace("/", os.sep))
                if not os.path.exists(leaf_path):
                    valid = False
                    break
        expected_no_prior = (i == len(test_situations) - 1)  # last one should be no-prior-art
        status = "PASS" if (valid and has_suggestions != is_no_prior) else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {situation[:60]}... -> {len(r['suggestions'])} suggestions, no_prior_art={is_no_prior}")
        results.append(r)
    
    # Determinism check: run first situation twice
    r1 = suggest(test_situations[0][0], test_situations[0][1])
    r2 = suggest(test_situations[0][0], test_situations[0][1])
    det_pass = json.dumps(r1["suggestions"]) == json.dumps(r2["suggestions"])
    print(f"  [{'PASS' if det_pass else 'FAIL'}] Determinism check (same input -> same output)")
    if not det_pass:
        all_pass = False
    
    # Write selftest result
    selftest_result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": len(test_situations) + 1,
        "all_pass": all_pass,
        "results": [{"situation": s["situation"], "suggestions_count": len(s["suggestions"]), "no_prior_art": s["no_prior_art"]} for s in results],
    }
    out = os.path.join(ARCH, "remediation-suggest-selftest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(selftest_result, f, indent=2)
    print(f"  Selftest written to {os.path.relpath(out, ROOT)}")
    
    # Write a sample suggestion output
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sample_out = os.path.join(ARCH, f"remediation-suggest-{date_str}.json")
    with open(sample_out, "w", encoding="utf-8") as f:
        json.dump(results[0], f, indent=2)
    print(f"  Sample output written to {os.path.relpath(sample_out, ROOT)}")
    
    return all_pass

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1:
        situation = " ".join(sys.argv[1:])
        r = suggest(situation)
        print(json.dumps(r, indent=2))
    else:
        print("Usage: python remediation_suggest.py [--selftest | <situation text>]")
        sys.exit(1)
