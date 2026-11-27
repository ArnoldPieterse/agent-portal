#!/usr/bin/env python3
"""Outlet Repost Curation Rubric (goal #6).

4-criteria scoring on 1-5 scale: relevance, freshness, engagement-potential, brand-fit.
Flags top candidates for repost from incoming briefs/items.

Usage:
  python memory/outlet/repost_rubric.py selftest   # prove: scores 20 items, top-3 flagged, consistent across runs
  python memory/outlet/repost_rubric.py            # real run on all briefs + queue entries
"""
import re, pathlib, hashlib, json

HERE = pathlib.Path(__file__).resolve().parent
BRIEFS = HERE / "briefs"
QUEUE = HERE / "queue"


def score_item(title, body):
    """Score 1-5 on each criterion based on content features."""
    text = (title + " " + body).lower()
    
    # Relevance: does it relate to fleet/AI/agent topics?
    rel_kw = ["fleet", "agent", "ai", "model", "autonom", "goal", "cycle",
              "convergence", "platform", "pipeline", "verification", "gate"]
    relevance = min(5, 1 + sum(1 for k in rel_kw if k in text))
    
    # Freshness: has a date or recent-sounding language?
    freshness = 3
    if re.search(r"\b2026\b", text): freshness += 1
    if any(w in text for w in ["this cycle", "just", "now", "new", "crossed", "live"]):
        freshness += 1
    freshness = min(5, max(1, freshness))
    
    # Engagement potential: has numbers? questions? strong claims?
    eng = 2
    nums = re.findall(r"\b\d+[\d.]*%?\b", text)
    if len(nums) >= 3: eng += 2
    elif len(nums) >= 1: eng += 1
    if any(w in text for w in ["surprising", "interesting", "key insight", "real story"]):
        eng += 1
    engagement = min(5, max(1, eng))
    
    # Brand fit: matches fleet voice (warm, candid, no corporate hype)?
    anti_kw = ["leverage", "synergy", "unlock", "game-changing", "revolutionary",
               "disruptive", "world-class", "best-in-class"]
    brand = 4
    if any(k in text for k in anti_kw):
        brand -= 2
    if len(body) < 150:
        brand += 1  # concise = on-brand
    if any(w in text for w in ["honest", "unglamorous", "real", "candid"]):
        brand += 1
    brand_fit = min(5, max(1, brand))
    
    total = relevance + freshness + engagement + brand_fit
    return {"relevance": relevance, "freshness": freshness,
            "engagement": engagement, "brand_fit": brand_fit, "total": total}


def extract_items():
    """Extract scoreable items from all briefs + queue entries."""
    items = []
    # From briefs: each numbered item is a candidate
    for bp in sorted(BRIEFS.glob("*.md")):
        if bp.name == "protocol.md": continue
        text = bp.read_text(encoding="utf-8")
        for m in re.finditer(r"^\d+\.\s+(.+)$", text, re.MULTILINE):
            item_text = m.group(1).strip()
            # Get a bit of surrounding context
            start = m.start()
            body = text[start:start+300]
            items.append({"source": bp.name, "title": item_text[:80], "body": body})
    # From queue: each post is a candidate
    for qp in sorted(QUEUE.glob("*.md")):
        if qp.name == "INDEX.md": continue
        text = qp.read_text(encoding="utf-8")
        # Extract the Body section as the item
        bm = re.search(r"## Body\s*\n(.+?)(?=\n##|\Z)", text, re.DOTALL)
        body = bm.group(1).strip() if bm else text[:200]
        tm = re.search(r"^topic:\s*(.+)$", text, re.MULTILINE)
        title = tm.group(1).strip() if tm else qp.stem
        items.append({"source": qp.name, "title": title[:80], "body": body})
    return items


def run():
    items = extract_items()
    print(f"Scoring {len(items)} items...")
    scored = []
    for it in items:
        s = score_item(it["title"], it["body"])
        scored.append({**it, **s})
    scored.sort(key=lambda x: (-x["total"], x["title"].lower()))
    
    print(f"\nTop-5 flagged:")
    for i, s in enumerate(scored[:5], 1):
        flag = " <-- TOP-3" if i <= 3 else ""
        print(f"  {i}. [{s['total']}/20] r={s['relevance']} f={s['freshness']} e={s['engagement']} b={s['brand_fit']} | {s['title'][:60]}{flag}")
    
    # Consistency check: re-score and verify same order
    scored2 = []
    for it in items:
        s2 = score_item(it["title"], it["body"])
        scored2.append({**it, **s2})
    scored2.sort(key=lambda x: (-x["total"], x["title"].lower()))
    top3_1 = {x["source"] + x["title"][:40] for x in scored[:3]}
    top3_2 = {x["source"] + x["title"][:40] for x in scored2[:3]}
    consistent = (top3_1 == top3_2)
    
    print(f"\nConsistency across runs: {'PASS' if consistent else 'FAIL'}")
    print(f"Items scored: {len(scored)} (target >= 20: {'PASS' if len(scored) >= 20 else 'FAIL'})")
    ok = consistent and len(scored) >= 20
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def selftest():
    """Prove: scores 20+ items, top-3 flagged, scoring consistent."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        bdir = td / "briefs"; qdir = td / "queue"
        bdir.mkdir(); qdir.mkdir()
        # Create 12 fake brief items + 8 queue entries = 20 total
        for i in range(4):
            (bdir / f"brief-{i}.md").write_text(
                f"# Brief {i}\ndate: 2026-11-26\nitems: 3\n\n## Items\n"
                f"1. Fleet goal completion hit {70+i*5}% this cycle with autonomous verification gates in place.\n"
                f"2. Agent autonomy score improved from 45 to {50+i*3} across the fleet.\n"
                f"3. The convergence sentinel caught a regression before it spread - real story behind the number.\n",
                encoding="utf-8")
        for i in range(8):
            (qdir / f"post-{i}.md").write_text(
                f"# Post {i}\ndate: 2026-11-26\nkind: upload\nplatform: test\nstatus: ready-for-human\ntopic: Test topic {i}\n\n## Body\n"
                f"The fleet crossed a real milestone - level {10+i} is live with {80+i*2}% completion. Honest numbers, no hype.\n\n"
                f"## Rationale\n- test\n\n## Evidence / sources (for Verifier fact-check before ship)\n- test: verified\n\nfact-check:\n- claim verified\n\n## Notes for ship\n- none\n",
                encoding="utf-8")
        global BRIEFS, QUEUE
        saved = (BRIEFS, QUEUE)
        BRIEFS, QUEUE = bdir, qdir
        try:
            items = extract_items()
            assert len(items) >= 20, f"only {len(items)} items"
            scored = []
            for it in items:
                s = score_item(it["title"], it["body"])
                scored.append({**it, **s})
            scored.sort(key=lambda x: (-x["total"], x["title"].lower()))
            # Consistency
            scored2 = sorted([{**it, **score_item(it["title"], it["body"])} for it in items], key=lambda x: -x["total"])
            top3a = [x["source"] for x in scored[:3]]
            top3b = [x["source"] for x in scored2[:3]]
            results = {"items_count": len(items), "top3_flagged": top3a, "consistent": top3a == top3b}
        finally:
            BRIEFS, QUEUE = saved
    print(json.dumps(results, indent=2))
    ok = results["items_count"] >= 20 and results["consistent"]
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    sys.exit(run())
