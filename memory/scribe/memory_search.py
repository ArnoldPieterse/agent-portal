#!/usr/bin/env python3
"""Institutional Memory Search (Scribe goal 9).

Full-text search across the memory/ tree (+ top-level TODO.md / MEMORY.md) with
ranking = relevance + recency + agent-role match. Returns top-N results, each a
{path, score, snippet, mtime} record.

Standalone usage:
    python memory/scribe/memory_search.py --q "hotload" --top 5

Importable (used by agent_portal.py /api/memory/search):
    from memory_search import search_memory
    results = search_memory("hotload", top=5, agent_role="Scribe")

Design notes:
- Relevance: sum of per-term occurrence counts; an exact whole-substring match of the
  full query gets a bonus so precise lookups rank first (no false negatives on exact terms).
- Recency: files modified within RECENT_DAYS get a decaying bonus (newer = higher).
- Role match: if a query term equals an agent name, files under that agent's dir or that
  mention the name prominently get a bonus - helps "what does Researcher know about X".
- Bounded + safe: skips binary/noise dirs, caps per-file read size, never raises on a bad file.
"""
import os
import re
import time
import json
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (memory/scribe/..)
MEMORY_DIR = os.path.join(HERE, "memory")
TOP_LEVEL_DOCS = ["TODO.md", "MEMORY.md"]  # live plan + hot file, searchable alongside memory/

SKIP_DIRS = {"__pycache__", ".git", ".unsloth-tmp", "unsloth-tmp", "AppData", "Microsoft", "Python"}
EXTS = {".md", ".json", ".jsonl", ".py", ".txt", ".css", ".js", ".html"}
MAX_FILE_BYTES = 200_000  # cap per-file read (memory files are small by design)
RECENT_DAYS = 30
SNIPPET_LEN = 160

# Fleet agent names for role-matching (kept in sync with agents.json).
AGENT_NAMES = ["Orchestrator", "Researcher", "Builder", "Verifier",
               "Designer", "Archivist", "Scribe", "Mechanic"]

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def _rel_under(base, full):
    """String-based relative path (avoids os.path.relpath failing across drive letters,
    e.g. sandbox Z: mapped to repo C:). Returns None if `full` is not under `base`."""
    base = base.replace("\\", "/").rstrip("/")
    full = full.replace("\\", "/")
    if full == base:
        return None
    if full.startswith(base + "/"):
        return full[len(base) + 1:]
    return None


def _iter_files():
    """Yield (abs_path, rel_path) for every searchable file under memory/ + top-level docs.
    rel_path is relative to the repo root (memory/... or TODO.md)."""
    seen = set()
    base = os.path.realpath(MEMORY_DIR)
    if os.path.isdir(base):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in SKIP_DIRS]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in EXTS:
                    continue
                full = os.path.realpath(os.path.join(dirpath, fn))
                if full in seen:
                    continue
                seen.add(full)
                rel = _rel_under(base, full)
                if rel is None:
                    continue
                yield full, "memory/" + rel
    # top-level live docs (relative to repo root)
    for doc in TOP_LEVEL_DOCS:
        full = os.path.realpath(os.path.join(HERE, doc))
        if os.path.isfile(full) and full not in seen:
            seen.add(full)
            yield full, doc


def _snippet(text, terms):
    """Return a ~SNIPPET_LEN window around the line with the highest term density."""
    best_line, best_hits = "", -1
    for line in text.splitlines():
        low = line.lower()
        hits = sum(low.count(t) for t in terms)
        if hits > best_hits:
            best_hits, best_line = hits, line.strip()
    line = best_line or (text.strip().splitlines() or [""])[0]
    if len(line) <= SNIPPET_LEN:
        return line
    # center on first term occurrence if present, else head
    low = line.lower()
    idx = min((low.find(t) for t in terms if t in low), default=0)
    start = max(0, idx - SNIPPET_LEN // 3)
    frag = line[start:start + SNIPPET_LEN].strip()
    return ("..." if start > 0 else "") + frag + ("..." if start + SNIPPET_LEN < len(line) else "")


def search_memory(query, top=5, agent_role=None):
    """Search memory/ for `query`. Returns a list of result dicts (best first)."""
    query = (query or "").strip()
    if not query:
        return []
    terms = _tokenize(query)
    if not terms:
        return []
    q_lower = query.lower()
    now = time.time()
    # agent names present in the query -> role-match candidates
    role_terms = [t for t in terms if any(t == a.lower() for a in AGENT_NAMES)]
    results = []
    for full, rel in _iter_files():
        try:
            st = os.stat(full)
            mtime = st.st_mtime
            with open(full, "rb") as fh:
                raw = fh.read(MAX_FILE_BYTES)
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            continue
        low = text.lower()
        # relevance: per-term frequency (cap each term's contribution to avoid one-word blowups)
        rel_score = 0.0
        for t in terms:
            c = low.count(t)
            if c:
                rel_score += min(c, 25) + (10.0 if c >= 3 else 0.0)
        # exact full-query substring bonus (precise lookups rank first)
        if q_lower in low:
            rel_score += 40.0
        if rel_score <= 0 and not (q_lower in low):
            continue  # no term hit at all -> skip
        # recency: decaying bonus for files touched within RECENT_DAYS
        age_days = max(0.0, (now - mtime) / 86400.0)
        if age_days <= RECENT_DAYS:
            recency = 15.0 * (1.0 - age_days / RECENT_DAYS)
        else:
            recency = 0.0
        # role match: query names an agent AND this file is in that agent's lane or about it
        role_bonus = 0.0
        for rt in role_terms:
            if ("/" + rt.lower() + "/") in ("/" + rel.lower() + "/"):
                role_bonus += 12.0
            elif low.count(rt) >= 3:
                role_bonus += 6.0
        # optional caller-side agent_role: nudge that agent's own lane up slightly
        if agent_role and ("/" + agent_role.lower() + "/") in ("/" + rel.lower() + "/"):
            role_bonus += 4.0
        score = round(rel_score + recency + role_bonus, 2)
        results.append({
            "path": rel,
            "score": score,
            "snippet": _snippet(text, terms),
            "mtime": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"),
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top]


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Institutional memory search")
    ap.add_argument("--q", required=True, help="query text")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--agent-role", default=None, help="optional agent name to nudge ranking")
    args = ap.parse_args()
    res = search_memory(args.q, top=args.top, agent_role=args.agent_role)
    print(json.dumps({"query": args.q, "count": len(res), "results": res}, indent=2))


if __name__ == "__main__":
    main()
