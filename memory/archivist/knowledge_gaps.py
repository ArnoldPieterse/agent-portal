#!/usr/bin/env python3
"""archivist/knowledge_gaps.py (cycle-5 goal 8).
Recurring topics with NO corresponding KB entry.
Topic signals: (a) goal titles from every memory/goals/*.md (a title recurring across
>1 file/cycle is a recurring topic); (b) human journal prompts (non-AUTO-LOOP) matching
the same words. A topic is COVERED when some memory/ leaf outside memory/goals/ has a
filename carries >=2 of its distinctive words; otherwise it is a gap.
Writes memory/archivist/knowledge_gaps.md (top gaps, each with suggested title +
sources to research). Exit 0 always."""
import json, os, re, time
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
STOP = set("""the a an and or of to in for with on at by from as is are was were be been this
that these those it its into over under per via not no yes can could may goal goals agent
agents seat cycle cycles run runs pass passes work done todo verify verified close closed
closing evidence record records logging log logs md file files python auto loop batch idle
human need needs needed next step steps then than so if when while after before during each
every all any some more most other others new old updated update updates add added adds make
makes made build built builds fix fixed fixes running ran test tested tests check checked
checks ensure ensures ensured using use used without within across between against about
above below here there which who whom what how why where do does did doing get gets got have
has had having let lets""".split())

def words(s):
    return [w for w in re.findall(r"[a-z][a-z0-9]{3,}", s.lower()) if w not in STOP]

def main():
    kb = []
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        relr = os.path.relpath(r, ROOT).replace("\\", "/")
        parts = relr.split("/")
        if len(parts) > 1 and parts[1] == "goals":
            continue
        for f in fs:
            if not f.endswith(".md"):
                continue
            p = os.path.join(r, f)
            try:
                first = open(p, encoding="utf-8", errors="replace").readline().strip()
            except Exception:
                continue
            name = os.path.relpath(p, ROOT).replace("\\", "/")
            toks = re.findall(r"[a-z0-9]{4,}", f.lower())
            kb.append((name, toks))

    def covered(title):
        # A topic is covered when some KB leaf's FILENAME carries >=2 of its
        # distinctive words (sentence-style H1s are too loose a signal).
        ws = words(title)
        if len(ws) < 2:
            return True
        return any(sum(1 for w in ws if w in toks) >= 2 for _, toks in kb)

    title_srcs = defaultdict(set)
    gdir = os.path.join(MEM, "goals")
    for r, d, fs in os.walk(gdir):
        for f in fs:
            if not f.endswith(".md"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for m in re.finditer(r"^\s*(?:\d+[.)]\s*)?\*\*([A-Z][^*\n]{6,70})\*\*\s*[-:]", txt, re.M):
                t = m.group(1).strip().rstrip("*").strip()
                if words(t):
                    title_srcs[t].add(rel)

    prompt_hits = defaultdict(set)
    rdir = os.path.join(ROOT, "runs")
    if os.path.isdir(rdir):
        for f in os.listdir(rdir):
            if not f.endswith(".journal"):
                continue
            p = os.path.join(rdir, f)
            try:
                lines = open(p, encoding="utf-8", errors="replace")
            except Exception:
                continue
            with lines:
                for line in lines:
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    pr = str(e.get("prompt") or "")
                    if not pr or pr.startswith("AUTO-LOOP"):
                        continue
                    pw = set(words(pr[:300]))
                    for t in title_srcs:
                        tw = set(words(t))
                        if len(tw & pw) >= max(2, len(tw) // 2):
                            prompt_hits[t].add(f)

    gaps = []
    for t, srcs in title_srcs.items():
        allsrc = srcs | prompt_hits.get(t, set())
        recurring = len(srcs) >= 2 or (prompt_hits.get(t) and len(allsrc) >= 2)
        if not recurring or covered(t):
            continue
        gaps.append((len(allsrc), t, sorted(allsrc)))
    gaps.sort(key=lambda g: (-g[0], g[1].lower()))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_gaps.md")
    L = ["# Knowledge gap report - %s" % time.strftime("%Y-%m-%d"),
         "Recurring topics (goal titles across cycles and/or human prompts) with NO KB leaf",
         "outside memory/goals/ sharing >=2 distinctive words. Top %d of %d gaps."
         % (min(len(gaps), 15), len(gaps)), ""]
    for i, (n, t, srcs) in enumerate(gaps[:15], 1):
        L.append("## %d. Suggested title: \"%s\"" % (i, t))
        L.append("- mentions: %d source file(s) (goal files + journal runs)" % n)
        L.append("- sources to research:")
        for s in srcs[:4]:
            L.append("  - %s" % s)
        L.append("")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("knowledge_gaps: %d gaps; top %d -> %s" % (len(gaps), min(len(gaps), 15), os.path.relpath(out, ROOT)))
    for n, t, s in gaps[:8]:
        print("   %2d sources  %s" % (n, t))

if __name__ == "__main__":
    main()
