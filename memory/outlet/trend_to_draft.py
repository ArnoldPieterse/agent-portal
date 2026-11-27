#!/usr/bin/env python3
"""Outlet Trend-to-Draft Pipeline (goal #3).

Takes a trend brief from memory/outlet/briefs/ and produces a skeleton post
in fleet default voice. Runs voice_lint on the output. Times each step.

Usage:
  python memory/outlet/trend_to_draft.py <brief_file>   # convert one brief
  python memory/outlet/trend_to_draft.py selftest       # prove full pipeline in temp dir
"""
import json, sys, datetime, pathlib, re, time

HERE = pathlib.Path(__file__).resolve().parent
BRIEFS = HERE / "briefs"
QUEUE = HERE / "queue"


def parse_brief(text):
    """Extract items from a trend brief. Returns list of {claim, source, confidence}."""
    items = []
    # Match numbered items: "N. **claim** ... — source: X — confidence: Y"
    pattern = re.compile(r'^\d+\.\s+(.*?)(?:—\s*source:\s*(.*?)\s*(?:—\s*confidence:\s*(.*?))?\s*$)', re.MULTILINE)
    for m in pattern.finditer(text):
        full_text = m.group(1).strip()
        source = (m.group(2) or "").strip()
        confidence = (m.group(3) or "").strip()
        # Extract the bold claim
        bold_match = re.search(r'\*\*(.+?)\*\*', full_text)
        claim = bold_match.group(1) if bold_match else full_text[:120]
        items.append({"claim": claim, "source": source, "confidence": confidence,
                      "full": full_text[:300]})
    return items


def skeleton_from_brief(items, date_str):
    """Generate a skeleton post from parsed brief items. Fleet voice: one concrete claim per post."""
    if not items:
        return None
    # Pick the strongest item (first with highest confidence, or just first)
    top = items[0]
    # Draft in fleet voice: warm, candid, lightly witty, one concrete claim
    body = (f"Here's the number that stuck: {top['claim']} "
            f"The rest of the story is less exciting - most teams are still figuring out "
            f"how to make it work past the demo phase. We're in that middle, which is where "
            f"the interesting decisions live.")
    
    slug = re.sub(r'[^a-z0-9-]', '-', top['claim'].lower()[:40].strip())
    fname = f"{date_str}-trend-{slug}.md"
    n = 1
    while (QUEUE / fname).exists():
        fname = f"{date_str}-trend-{slug}-{n}.md"
        n += 1
    
    sources_list = "\n".join(f"- {it['claim'][:80]}: {it['source']} ({it['confidence']})" for it in items[:3])
    post = f"""# Staged post: trend observation
date: {date_str}
kind: upload
platform: (unregistered - awaiting Arnold connection; fleet default voice)
status: ready-for-human
topic: Trend - {top['claim'][:60]}

## Body
{body}

## Rationale
- Auto-drafted by trend_to_draft.py from brief items.
- One concrete claim: "{top['claim'][:100]}"
- Fleet voice: warm, candid, zero hype, one number.

## Evidence / sources (for Verifier fact-check before ship)
{sources_list}

fact-check:
- claim: {top['claim'][:80]} -> source: {top['source']} (confidence: {top['confidence']})
- PENDING Verifier sign-off before ship.

## Notes for ship
- No internal IPs, paths, keys or secrets in body.
- Needs platform + human approval before ship.
"""
    return fname, post


def voice_lint_check(text):
    """Inline voice lint: length cap + banned phrases. Returns (pass, failures)."""
    failures = []
    body_match = re.search(r'## Body\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if body_match:
        body = body_match.group(1).strip()
        if len(body) > 600:
            failures.append(f"body {len(body)} chars > 600 cap")
    banned = ["synergy", "leverage our ecosystem", "game-changer", "disruptive",
              "cutting-edge solution", "world-class", "best-in-class", "innovative platform"]
    for b in banned:
        if b in text.lower():
            failures.append(f"banned phrase: '{b}'")
    return len(failures) == 0, failures


def process_brief(brief_path):
    """Full pipeline: read brief -> parse -> skeleton -> lint. Returns result dict."""
    t0 = time.time()
    text = pathlib.Path(brief_path).read_text(encoding="utf-8")
    items = parse_brief(text)
    if not items:
        return {"brief": str(brief_path), "ok": False, "error": "no items parsed", "time_s": 0}
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    result = skeleton_from_brief(items, date_str)
    if not result:
        return {"brief": str(brief_path), "ok": False, "error": "no skeleton generated", "time_s": time.time()-t0}
    
    fname, post = result
    QUEUE.mkdir(parents=True, exist_ok=True)
    (QUEUE / fname).write_text(post, encoding="utf-8")
    
    lint_pass, lint_failures = voice_lint_check(post)
    elapsed = time.time() - t0
    
    return {"brief": str(brief_path), "ok": True, "draft": fname,
            "items_parsed": len(items), "lint_pass": lint_pass, "lint_failures": lint_failures,
            "time_s": round(elapsed, 2)}


def selftest():
    """Prove pipeline works: takes a brief, produces a draft, passes lint."""
    import tempfile
    results = {"draft_produced": False, "lint_pass": False, "under_5min": False}
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        qd = td / "queue"
        qd.mkdir()
        global QUEUE
        saved_q = QUEUE
        QUEUE = qd
        try:
            # Write a test brief
            test_brief = ("# Test brief\ndate: 2026-11-26\nkind: trend-brief\nsource: selftest\nitems: 2\n\n"
                         "## Items\n"
                         "1. **87% of developers now use AI coding assistants daily** - up from 50% last quarter, per Stack Overflow survey. — source: Stack Overflow Dev Survey 2026 (https://example.com) — confidence: verified.\n\n"
                         "2. **Median time to production for agent systems dropped to 3 weeks** - down from 8 weeks in early 2026. — source: internal fleet data — confidence: high.\n")
            brief_f = td / "test-brief.md"
            brief_f.write_text(test_brief, encoding="utf-8")
            
            r = process_brief(brief_f)
            results["draft_produced"] = r.get("ok", False) and (qd / r.get("draft", "")).exists()
            results["lint_pass"] = r.get("lint_pass", False)
            results["under_5min"] = r.get("time_s", 999) < 300
        finally:
            QUEUE = saved_q
    
    print(json.dumps(results, indent=2))
    ok = all(results.values())
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    cmd = sys.argv[1]
    if cmd == "selftest":
        return selftest()
    # Try as full path first, then in briefs/ dir
    p = pathlib.Path(cmd)
    if p.exists():
        r = process_brief(p)
    elif (BRIEFS / cmd).exists():
        r = process_brief(BRIEFS / cmd)
    else:
        print(f"Brief not found: {cmd}"); return 1
    print(json.dumps(r, indent=2))
    return 0 if r.get("ok") else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
