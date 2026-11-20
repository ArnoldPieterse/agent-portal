#!/usr/bin/env python3
"""Card Staleness Detection (Scribe goal #5, cycle-8).

Checks every reference card in memory/scribe/cards/. For each card it extracts the
source files it cites (via inline `_Source: `path`` lines and the trailing
"Sources (by relevance)" list), then compares each cited source's mtime against the
card's own mtime. A cited source whose mtime is NEWER than the card means that source
changed after the card was generated -> the card may be stale.

Output (stdout JSON): a list of
    {card_path, stale_sources[], last_generated, days_since}
for every card (stale_sources empty when fresh). Exit code 0 always; use --strict to
exit 1 if any card has stale sources.

Usage:
    python memory/scribe/card_staleness.py            # JSON report over all cards
    python memory/scribe/card_staleness.py --strict   # exit 1 if any stale
    python memory/scribe/card_staleness.py --selftest # run acceptance tests in a temp tree
"""
import os
import re
import sys
import json
import time
import shutil
import tempfile
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))          # .../memory/scribe
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))     # repo root (holds memory/)
CARDS_DIR = os.path.join(HERE, "cards")

# Tolerance: ignore sub-second mtime jitter from mirror sync.
TOL_S = 2.0

SRC_INLINE = re.compile(r"_Source:\s*`([^`]+)`", re.IGNORECASE)
SRC_LIST = re.compile(r"^-\s*`([^`]+)`", re.MULTILINE)
GEN_LINE = re.compile(r"_Generated:\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def _norm(p):
    """Normalize a cited source path to an absolute path under ROOT."""
    p = p.strip().strip("`").replace("\\", "/")
    if os.path.isabs(p):
        return os.path.normpath(p)
    # Cited paths are repo-root-relative (e.g. memory/scribe/foo.md).
    return os.path.normpath(os.path.join(ROOT, p))


def extract_sources(text):
    """Return the ordered-unique list of cited source paths in a card."""
    seen = []
    for m in SRC_INLINE.finditer(text):
        seen.append(m.group(1).strip())
    # Also pull from the trailing 'Sources (by relevance)' bullet list.
    tail = text.split("## Sources", 1)
    if len(tail) == 2:
        for m in SRC_LIST.finditer(tail[1]):
            seen.append(m.group(1).strip())
    out = []
    for s in seen:
        if s and s not in out:
            out.append(s)
    return out


def parse_generated(text, card_mtime):
    m = GEN_LINE.search(text)
    if m:
        return m.group(1)
    return date.fromtimestamp(card_mtime).isoformat()


def check_card(card_path, now=None):
    now = now or time.time()
    with open(card_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    card_mtime = os.path.getmtime(card_path)
    stale = []
    for src in extract_sources(text):
        ap = _norm(src)
        if not os.path.exists(ap):
            continue  # cited source gone -> not a mtime-staleness signal here
        smt = os.path.getmtime(ap)
        if smt > card_mtime + TOL_S:
            stale.append({
                "source": src,
                "src_mtime": datetime.fromtimestamp(smt).isoformat(timespec="seconds"),
                "card_mtime": datetime.fromtimestamp(card_mtime).isoformat(timespec="seconds"),
            })
    return {
        "card_path": os.path.relpath(card_path, ROOT).replace("\\", "/"),
        "stale_sources": stale,
        "last_generated": parse_generated(text, card_mtime),
        "days_since": int((now - card_mtime) // 86400),
    }


def run(cards_dir=CARDS_DIR, now=None):
    results = []
    if not os.path.isdir(cards_dir):
        return results
    for fn in sorted(os.listdir(cards_dir)):
        if not fn.endswith(".md"):
            continue
        results.append(check_card(os.path.join(cards_dir, fn), now=now))
    return results


def main(argv):
    strict = "--strict" in argv
    selftest = "--selftest" in argv
    if selftest:
        return _selftest()
    results = run()
    print(json.dumps(results, indent=2))
    if strict and any(r["stale_sources"] for r in results):
        return 1
    return 0


def _selftest():
    """Acceptance tests in an isolated temp tree (never touches real cards)."""
    tmp = tempfile.mkdtemp(prefix="card_staleness_selftest_")
    try:
        # Build a fake repo layout: <tmp>/memory/scribe/cards + cited sources.
        scribe = os.path.join(tmp, "memory", "scribe")
        cards = os.path.join(scribe, "cards")
        srcdir = os.path.join(tmp, "memory", "ops")
        os.makedirs(cards)
        os.makedirs(srcdir)

        # Source A (cited by card1), source B (cited by card2).
        src_a = os.path.join(srcdir, "a.md")
        src_b = os.path.join(srcdir, "b.md")
        with open(src_a, "w") as f:
            f.write("alpha\n")
        with open(src_b, "w") as f:
            f.write("beta\n")

        card1 = os.path.join(cards, "c1.md")
        card2 = os.path.join(cards, "c2.md")
        with open(card1, "w") as f:
            f.write("# c1\n_Generated: 2026-11-20 | Sources: 1 files | Key facts: 1_\n"
                    "fact one\n   _Source: `memory\\ops\\a.md`_\n")
        with open(card2, "w") as f:
            f.write("# c2\n_Generated: 2026-11-20 | Sources: 1 files | Key facts: 1_\n"
                    "fact two\n   _Source: `memory\\ops\\b.md`_\n")

        # Backdate sources older than the cards; backdate cards an hour ago so a
        # fresh source edit (now) is unambiguously newer than the card (clear of
        # the 2s sync tolerance).
        past = time.time() - 3600
        for c in (card1, card2):
            os.utime(c, (past, past))
        older = past - 600
        for s in (src_a, src_b):
            os.utime(s, (older, older))

        # Point module ROOT/CARDS at the temp tree.
        global ROOT, CARDS_DIR
        saved_root, saved_cards = ROOT, CARDS_DIR
        ROOT, CARDS_DIR = tmp, cards
        try:
            # --- Test 1: fresh run -> no card flagged (no false positives).
            r = run(cards_dir=cards)
            by_card = {x["card_path"]: x for x in r}
            assert len(r) == 2, "expected 2 cards"
            assert all(x["stale_sources"] == [] for x in r), \
                "fresh run must flag nothing: %r" % [x for x in r if x["stale_sources"]]

            # --- Test 2: modify a cited source -> its card is flagged.
            time.sleep(0.05)
            with open(src_a, "a") as f:
                f.write("alpha-changed\n")
            os.utime(src_a)  # ensure mtime strictly newer
            r2 = run(cards_dir=cards)
            by_card2 = {x["card_path"]: x for x in r2}
            c1 = [x for x in r2 if "c1.md" in x["card_path"]][0]
            c2 = [x for x in r2 if "c2.md" in x["card_path"]][0]
            assert any("a.md" in s["source"] for s in c1["stale_sources"]), \
                "modified source a.md must flag card c1: %r" % c1
            assert c2["stale_sources"] == [], \
                "unmodified card c2 must NOT be flagged: %r" % c2

            # --- Test 3: output shape + valid fields.
            for x in r2:
                assert set(["card_path", "stale_sources", "last_generated", "days_since"]) <= set(x)
                assert isinstance(x["days_since"], int)
                assert re.match(r"\d{4}-\d{2}-\d{2}$", x["last_generated"])

            print("SELFTEST PASS: 3/3 acceptance criteria met")
            print("  - fresh run flags nothing (no false positives)")
            print("  - modified source a.md -> card c1 flagged, c2 clean")
            print("  - JSON shape valid for all cards")
            return 0
        finally:
            ROOT, CARDS_DIR = saved_root, saved_cards
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
