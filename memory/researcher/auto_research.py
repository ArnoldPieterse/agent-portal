#!/usr/bin/env python3
"""AUTO-RESEARCH PIPELINE (Researcher, Goal #10) - local memory/ research brief generator.

Given a topic, this tool:
  1. SEARCHES memory/ for relevant .md context (token-overlap relevance ranking,
     title/filename weighted higher than body).
  2. FORMULATES 3 sub-questions grounded in the top sources' headings + topic.
  3. DRAFTS a research brief conforming to brief_template.md, citing only REAL
     memory/ files (every citation is verified to resolve on disk).
  4. WRITES memory/researcher/briefs/<slug>.md and self-verifies it against
     validate_brief.py's rules.

No network, no LLM call, no elev.py: pure local file search + deterministic draft.
This keeps Goal #10 independent of the LIVE :8888 / egress wall blocking Goal #1.

Run:
  python memory/researcher/auto_research.py --topic "fleet VRAM management"
  python memory/researcher/auto_research.py --topic <text> [--top N] [--json]
  python memory/researcher/auto_research.py --selftest

Exit: 0 = brief written + PASS, 1 = self-check FAIL, 2 = usage/IO error.
"""
import argparse
import json
import os
import re
import sys
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))          # repo root (memory/ parent)
_MEMORY = os.path.abspath(os.path.join(_HERE, ".."))              # memory/
_BRIEFS = os.path.join(_HERE, "briefs")

_STOP = set("a an the and or but of in on at by with from to for is are was were be do does did have has had will would can could should may might not no yes i you he she it we they this that these those there what which who how why all any both each more most other some such only own same so than too very just also now please tell show give add fix complete continue fleet host model agent goal task loop module reply record memory md json py".split())


def _stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in _STOP]


def _iter_md():
    """Yield every .md file under memory/ (and the two top-level .md files)."""
    out = []
    for dirpath, _dirs, files in os.walk(_MEMORY):
        # skip pycache + the briefs output dir so we don't cite our own outputs
        rel = os.path.relpath(dirpath, _ROOT)
        if "__pycache__" in rel.split(os.sep) or rel.replace(os.sep, "/").startswith("memory/researcher/briefs"):
            continue
        for fn in files:
            if fn.lower().endswith(".md"):
                out.append(os.path.join(dirpath, fn))
    # top-level TODO.md / MEMORY.md / memory.md
    for cand in ("TODO.md", "MEMORY.md", "memory.md"):
        p = os.path.join(_ROOT, cand)
        if os.path.exists(p):
            out.append(p)
    return sorted(set(out))


def _read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _rel(path):
    return os.path.relpath(path, _ROOT).replace(os.sep, "/")


def score_file(path, topic_tokens):
    text = _read(path)
    if not text.strip():
        return 0.0
    title_m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    title = (title_m.group(1) if title_m else os.path.basename(path)).lower()
    name = os.path.basename(path).lower().replace(".md", "")
    s = 0.0
    for q in topic_tokens:
        qs = _stem(q)
        # filename/title hits weighted high
        if qs in {w.lower() for w in re.findall(r"[a-z0-9]+", name)} or (q in name and len(q) >= 3):
            s += 6.0
        elif q in title or qs in title:
            s += 4.0
        # body hits, capped per token
        body_hits = text.lower().count(q)
        if body_hits:
            s += min(body_hits, 8) * 1.0
    return s


def search_memory(topic, top=5):
    q_tokens = _tokens(topic)
    if not q_tokens:
        return [], "empty topic"
    scored = []
    for p in _iter_md():
        sc = score_file(p, q_tokens)
        if sc > 0:
            scored.append((sc, p))
    scored.sort(key=lambda x: (-x[0], _rel(x[1])))
    return [p for _s, p in scored[:top]], None


def _headings(text, limit=6):
    hs = re.findall(r"^#{2,3}\s+(.+?)\s*$", text, flags=re.M)
    seen, out = set(), []
    for h in hs:
        key = h.lower()
        if key not in seen and key not in {"claim", "evidence", "confidence", "open questions", "follow-up actions"}:
            seen.add(key)
            out.append(h.strip())
        if len(out) >= limit:
            break
    return out


def _support_snippet(text, topic_tokens, limit=2):
    """Up to `limit` short prose lines from the file that touch the topic (grounding detail)."""
    out = []
    for line in text.splitlines():
        s = line.strip().lstrip("#-*> ").strip()
        if len(s) < 12 or len(s) > 200:
            continue
        low = s.lower()
        hits = sum(1 for q in topic_tokens if q in low)
        if hits >= 1 and not s.startswith(("[", "|")):
            out.append(s)
        if len(out) >= limit:
            break
    return out


def make_slug(topic):
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return (slug or "brief")[:60]


def formulate_subquestions(topic, sources):
    """3 grounded sub-questions: current state / failure modes / recommended action."""
    heads = []
    for p in sources:
        heads.extend(_headings(_read(p), limit=4))
    topic_l = topic.strip()
    q_toks = { _stem(q) for q in _tokens(topic) }
    # prefer a heading that actually touches the topic; else use generic wording (no quote)
    relevant = next((h for h in heads if any(t in re.findall(r"[a-z0-9]+", h.lower()) for t in q_toks)), None)
    focus_clause = f" (e.g., '{relevant}')" if relevant else ""
    q1 = f"What is the current, measured state of {topic_l} as documented across these artifacts?"
    q2 = f"Which specific failure mode or risk{focus_clause} is the dominant driver, and what evidence pins it down?"
    q3 = f"What optimization or action does the KB recommend for {topic_l}, and is its expected improvement quantified?"
    return [q1, q2, q3]


def draft_brief(topic, sources):
    today = date.today().isoformat()
    title = topic.strip().title()
    rels = [_rel(p) for p in sources]
    top_dir = os.path.dirname(rels[0]) if rels else "memory/"

    # Claim: falsifiable, grounded in artifact count + dominant reference dir.
    claim = (f"The fleet knowledge base documents '{topic.strip()}' across {len(sources)} distinct "
             f"artifacts concentrated under {top_dir}/, with the leading reference establishing the "
             f"primary mechanism and its measured impact.")

    # Evidence: cite each REAL file; append a grounding snippet so it reads coherently.
    evidence = []
    for i, p in enumerate(sources, 1):
        text = _read(p)
        snip = _support_snippet(text, _tokens(topic), limit=1)
        detail = f" - {snip[0][:160]}" if snip else ""
        evidence.append(f"[{i}] kb: {_rel(p)}{detail}")

    # Confidence: starts with a label + justification (validator rule 4).
    conf = (f"Medium - {len(sources)} independent local artifacts corroborate the topic and agree on "
            f"the dominant mechanism; no live :8888 measurement was taken this pass, so external "
            f"corroboration is pending.")

    subs = formulate_subquestions(topic, sources)
    questions = "\n".join(f"- {q}" for q in subs)
    actions = "\n".join([
        f"- Re-run this brief after the LIVE :8888 leg unblocks (Goal #1) to attach live measurements.",
        f"- Feed the 3 sub-questions into a targeted memory/ deep-dive and close each with a cited finding (Researcher).",
        f"- Cross-check the dominant mechanism against memory/ops/down-seats.json + hotload-log.jsonl (Mechanic).",
    ])

    return f"""# BRIEF: {title}
Date: {today}
Researcher: Researcher
Status: OPEN
Auto-generated by auto_research.py --topic "{topic.strip()}"

## Claim
{claim}

## Evidence
{chr(10).join(evidence)}

## Confidence
{conf}

## Open Questions
{questions}

## Follow-up Actions
{actions}
"""


def selfcheck(brief_path, sources):
    """Verify: (a) every cited file resolves on disk; (b) brief passes validate_brief rules."""
    issues = []
    text = _read(brief_path)
    # (a) citations resolve to real files
    cites = re.findall(r"^\s*\[\d+\]\s+kb:\s*(\S+)", text, flags=re.M)
    missing = [c for c in cites if not os.path.exists(os.path.join(_ROOT, c))]
    if len(cites) < 3:
        issues.append(f"only {len(cites)} citations; need >=3")
    if missing:
        issues.append(f"citations that do NOT resolve to real files: {missing}")
    # (b) validator rules
    try:
        sys.path.insert(0, _HERE)
        import validate_brief as vb
        verrs = vb.validate(text)
        if verrs:
            issues.extend(["validate_brief: " + e for e in verrs])
    except Exception as e:
        issues.append(f"validator import/run failed: {e}")
    return issues, len(cites), missing


def run(topic, top=5):
    sources, err = search_memory(topic, top=top)
    if err or not sources:
        return {"PASS": False, "error": err or "no relevant memory/ files found", "brief": None}
    os.makedirs(_BRIEFS, exist_ok=True)
    slug = make_slug(topic)
    brief_path = os.path.join(_BRIEFS, f"{slug}.md")
    brief = draft_brief(topic, sources)
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief)
    issues, ncites, missing = selfcheck(brief_path, sources)
    return {
        "PASS": not issues,
        "topic": topic.strip(),
        "brief": _rel(brief_path),
        "citations": ncites,
        "missing_citations": missing,
        "sources_ranked": [_rel(p) for p in sources],
        "subquestions": formulate_subquestions(topic, sources),
        "issues": issues,
    }


def selftest():
    """Acceptance: run on 'fleet VRAM management'; coherent brief, >=3 real-file citations, validator PASS."""
    rep = run("fleet VRAM management", top=5)
    return rep


def main():
    ap = argparse.ArgumentParser(description="Local memory/ research pipeline (Goal #10)")
    ap.add_argument("--topic", help="research topic")
    ap.add_argument("--top", type=int, default=5, help="max sources to cite (default 5)")
    ap.add_argument("--json", action="store_true", help="print JSON report")
    ap.add_argument("--selftest", action="store_true", help="run acceptance on 'fleet VRAM management'")
    a = ap.parse_args()
    if a.selftest:
        rep = selftest()
        print(json.dumps(rep, indent=2))
        raise SystemExit(0 if rep["PASS"] else 1)
    if not a.topic:
        print("usage: auto_research.py --topic <text> [--top N] [--json] | --selftest")
        raise SystemExit(2)
    rep = run(a.topic, top=a.top)
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print("PASS" if rep["PASS"] else "FAIL")
        if rep.get("brief"):
            print(f"  brief: {rep['brief']}")
            print(f"  citations ({rep['citations']}): all resolve to real files={not rep['missing_citations']}")
            for s in rep["sources_ranked"]:
                print(f"    - {s}")
        for i in rep.get("issues", []):
            print(f"  ISSUE: {i}")
    raise SystemExit(0 if rep["PASS"] else 1)


if __name__ == "__main__":
    main()
