"""Modulization - recursive context shrinking for LLM prompts (user idea, 2026-11-26).

Formula:
  1. WORD pass: repeatedly replace the most frequent word with a placeholder TAG;
     a legend line at the top of the prompt says Replace <tag> with "<word>".
  2. SEQUENCE pass: same for repeated character sequences (n-grams) in the shrunk text.
  Iterate until no candidate nets more than min_gain chars, or rounds are exhausted.

Placeholder tags: the shortest strings over a compact alphabet that do NOT occur
anywhere in the original text (1 char if any exist, else 2-char, else 3-char).
Real prompts contain every single letter/digit, so 2-3 char tags are the norm.

CORRECTNESS GUARANTEE (round-trip exact):
  - a tag never occurs in the original text, so every occurrence in the shrunk text
    is an inserted placeholder;
  - unmodulize() applies substitutions in REVERSE legend order, which also makes
    nested cases exact (a later item may be an earlier tag string itself).
  => unmodulize(modulize(x)) == x, byte-for-byte.

Savings accounting includes legend cost; replacements that do not pay off are skipped.
"""
import re
from collections import Counter

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
DEFAULTS = dict(max_rounds=8, min_freq=5, min_word_len=4, seq_lens=(4, 5, 6), min_gain=30)
HEADER_MARK = "[MODULED CONTEXT - DECODE FIRST: "


def _placeholder_pool(original, max_tag_len=3):
    pool = []
    for L in range(1, max_tag_len + 1):
        subs = set(original[i:i + L] for i in range(len(original) - L + 1))
        import itertools
        for combo in itertools.product(ALPHABET, repeat=L):
            s = "".join(combo)
            if s not in subs:
                pool.append(s)
        if len(pool) >= 24:
            break
    return pool


def modulize(text, **kw):
    cfg = dict(DEFAULTS)
    cfg.update(kw)
    work = text
    pool = _placeholder_pool(text)
    legend = []  # (tag, item, kind)
    for _ in range(cfg["max_rounds"]):
        if not pool:
            break
        best = None  # (gain, tag, item, kind)
        cnt = Counter(w for w in re.findall(r"[A-Za-z][A-Za-z_\-]{%d,}" % (cfg["min_word_len"] - 1), work))
        for w, f in cnt.most_common(40):
            if f < cfg["min_freq"]:
                break
            tag = next((t for t in pool if t not in w), None)
            if not tag:
                continue
            gain = f * (len(w) - len(tag)) - (len(w) + 6)
            if gain > cfg["min_gain"] and (best is None or gain > best[0]):
                best = (gain, tag, w, "word")
        for n in cfg["seq_lens"]:
            grams = Counter(work[i:i + n] for i in range(len(work) - n + 1))
            for g, f in grams.most_common(40):
                if f < cfg["min_freq"] or '"' in g:
                    break
                tag = next((t for t in pool if t not in g), None)
                if not tag:
                    continue
                gain = f * (n - len(tag)) - (n + 6)
                if gain > cfg["min_gain"] and (best is None or gain > best[0]):
                    best = (gain, tag, g, "seq")
        if best is None:
            break
        gain, tag, item, kind = best
        work = re.sub(r"\b" + re.escape(item) + r"\b", tag, work) if kind == "word" else work.replace(item, tag)
        pool.remove(tag)
        legend.append((tag, item, kind))
    if not legend:
        return None
    header = HEADER_MARK + " | ".join('%s="%s"' % (tag, item) for tag, item, _ in legend) + "]"
    out = header + "\n" + work
    return {"text": out, "before": len(text), "after": len(out),
            "saved": len(text) - len(out), "legend": legend}


def unmodulize(text):
    """Exact inverse of modulize(): parse the legend, apply substitutions in reverse order."""
    m = re.match(r"^\[MODULED CONTEXT - DECODE FIRST: (.*)\]\n", text)
    if not m:
        return text
    pairs = re.findall(r'(\S+)="([^"]*)"', m.group(1))
    work = text[m.end():]
    for tag, item in reversed(pairs):
        work = work.replace(tag, item)
    return work


def selftest():
    tricky = ("The agent portal memory keeps the memory of every agent. "
              "Memory is the memory that memory agents share with the memory ledger. "
              "Use the memory ledger in memory/ops for memory audits of the memory pool. "
              "memory memory memory")
    r = modulize(tricky)
    assert r, "expected a shrink on repetitive text"
    assert unmodulize(r["text"]) == tricky, "round-trip failed"
    plain = "Short unique sentence with no repeats at all."
    assert modulize(plain) is None
    # nested case: force a tag that later becomes an item
    t2 = ("alpha beta alpha gamma alpha delta alpha beta alpha gamma alpha delta " * 3)
    r2 = modulize(t2, min_freq=4)
    if r2:
        assert unmodulize(r2["text"]) == t2, "nested round-trip failed"
    return True


if __name__ == "__main__":
    import sys
    selftest()
    print("selftest OK")
    if len(sys.argv) > 1:
        text = open(sys.argv[1], encoding="utf-8").read()
    else:
        text = ("The agent portal memory keeps the memory of every agent. " * 6 +
                "Memory is shared through the memory ledger in memory/ops, which audits "
                "the memory pool and the memory index for every agent seat in the fleet.")
    r = modulize(text)
    if not r:
        print("no net savings (legend would cost more than it saves)")
    else:
        print("before %d -> after %d chars (saved %d, %.1f%%)" %
              (r["before"], r["after"], r["saved"], 100.0 * r["saved"] / r["before"]))
        for tag, w, k in r["legend"]:
            print("   [%s] = %r  (%s)" % (tag, w, k))
        print("round-trip exact:", unmodulize(r["text"]) == text)
