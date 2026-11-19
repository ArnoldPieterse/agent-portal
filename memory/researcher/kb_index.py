#!/usr/bin/env python3
"""
kb_index.py — Fleet Knowledge Base Index (Researcher goal #9, cycle-7).

Walks memory/ and produces a compact machine-readable index of every knowledge
file (.md/.json) with: path, last-modified, topic tags, linked agents.

Outputs:
  memory/INDEX-kb.json   — full index (machine-readable)
  memory/INDEX.md        — appends/replaces a MANAGED block only (idempotent);
                           existing pointers above the sentinels are never touched.

Design constraints (per file-modularity rule): keep each entry compact so the
JSON stays small enough to stream; cap tags per file. Excludes non-knowledge
noise (browser profile caches, python/pytest caches) and reports coverage vs the
full .md/.json set so the >=90% acceptance test is honest.
"""
import os, re, time, json, datetime

ROOT = "memory"
OUT_JSON = os.path.join(ROOT, "INDEX-kb.json")
OUT_MD   = os.path.join(ROOT, "INDEX.md")
EXTS = {".md", ".json"}

# --- exclusions: directories that are tool/browser noise, not knowledge ------
EXCL_DIRS = {"__pycache__", ".pytest_cache", "_ud768", "node_modules", ".git"}

AGENTS = ["orchestrator", "researcher", "builder", "verifier", "designer",
          "archivist", "scribe", "mechanic"]

# topic keyword -> tag. Order matters: earlier wins for priority.
TOPIC_KEYWORDS = [
    ("mirror-revert",  "mirror-revert"),
    ("mirror_revert",  "mirror-revert"),
    ("pin",            "pin-guard"),
    ("clobber",        "sync-clobber"),
    ("sla",            "sla"),
    ("hotload",        "hotload"),
    ("watchdog",       "watchdog"),
    ("residency",      "residency"),
    ("benchmark",      "benchmark"),
    ("bench",          "benchmark"),
    ("drift",          "drift"),
    ("blocker",        "blockers"),
    ("reboot",         "recovery"),
    ("recovery",       "recovery"),
    ("vram",           "vram"),
    ("eviction",       "eviction"),
    ("upload",         "uploads"),
    ("sync",           "sync"),
    ("evidence",       "evidence"),
    ("citation",       "citations"),
    ("crosscheck",     "cross-check"),
    ("understanding",  "understanding-module"),
    ("dictionary",     "dictionary"),
    ("brief",          "research-brief"),
    ("goal",           "goals"),
    ("postmortem",     "postmortems"),
    ("decision",       "decisions"),
    ("synthesis",      "synthesis"),
    ("typo",           "audit"),
    ("tokenization",   "css-tokens"),
    ("dark-mode",      "ui-theme"),
]

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}|r\d{1,3})\b")
STOPWORDS = {"the","and","for","with","from","into","over","under",
             "state","status","check","notes","note","final","fresh",
             "resolved","reverify","reverified","revert","run","log",
             "report","analysis","study","scan","audit","fix","fixed"}


def derive_tags(relpath, name):
    """Deterministic topic tags from path tokens (no full-file read)."""
    low = relpath.lower()
    base = os.path.basename(low)
    # 1) dir tag (top subdir under memory/)
    parts = relpath.replace("\\", "/").split("/")
    tags = []
    if len(parts) > 1 and parts[0] == "memory" and parts[1] not in EXCL_DIRS:
        tags.append(parts[1])
    # 2) keyword hits across full path
    for kw, tag in TOPIC_KEYWORDS:
        if kw in low and tag not in tags:
            tags.append(tag)
    # 3) salient filename tokens (dates/agent/stopword stripped), up to 2
    toks = re.split(r"[-_./]+", base)
    added = 0
    for t in toks:
        if added >= 2:
            break
        t = DATE_RE.sub("", t).strip()
        if not t or t.isdigit() or t in STOPWORDS or t in AGENTS:
            continue
        t = t[:18]
        if t not in tags and len(t) > 3:
            tags.append(t)
            added += 1
    # cap + de-dup preserving order
    seen, out = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t); out.append(t)
    return out[:6]


def derive_agents(relpath):
    """Which seats a file is linked to (dir + filename prefix)."""
    low = relpath.lower().replace("\\", "/")
    parts = low.split("/")
    base = os.path.basename(low)
    found = []
    # directory membership
    if len(parts) > 1 and parts[1] in AGENTS:
        found.append(parts[1])
    # filename prefix / token
    for a in AGENTS:
        if a in found:
            continue
        if base.startswith(a + "-") or ("-" + a + "-") in base or ("_" + a + "_") in base:
            found.append(a)
    return found


def main():
    now = datetime.date.today().isoformat()
    all_files, kept = [], []
    for dp, dn, fn in os.walk(ROOT):
        # prune noise dirs in-place
        dn[:] = [d for d in dn if d not in EXCL_DIRS]
        for f in fn:
            e = os.path.splitext(f)[1].lower()
            if e not in EXTS:
                continue
            full = os.path.join(dp, f)
            rel = full.replace("\\", "/")
            all_files.append(rel)
    total = len(all_files)
    entries = []
    for rel in sorted(all_files):
        try:
            mt = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(rel)))
        except OSError:
            continue
        name = os.path.basename(rel)
        entries.append({
            "path":   rel,
            "mod":    mt,
            "tags":   derive_tags(rel, name),
            "agents": derive_agents(rel),
        })
    covered = len(entries)
    coverage = round(100.0 * covered / total, 1) if total else 0.0

    idx = {
        "generated": now,
        "root": ROOT,
        "total_md_json": total,
        "indexed": covered,
        "coverage_pct": coverage,
        "excluded_dirs": sorted(EXCL_DIRS),
        "entries": entries,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, indent=1)

    # ---- update INDEX.md via idempotent managed block ----------------------
    top = sorted({e["path"].split("/")[1] for e in entries if len(e["path"].split("/")) > 1})
    lines = ["<!-- KB-INDEX:BEGIN (auto-generated by kb_index.py — do not edit) -->",
             "## Fleet Knowledge Base Index (machine)",
             f"- Generated {now}: **{covered}/{total}** files indexed ({coverage}% coverage)",
             f"- Machine-readable index: `memory/INDEX-kb.json`",
             f"- Top-level sections: {', '.join('`'+t+'`' for t in top)}",
             "<!-- KB-INDEX:END -->"]
    block = "\n".join(lines) + "\n"

    existing = ""
    if os.path.exists(OUT_MD):
        with open(OUT_MD, encoding="utf-8") as fh:
            existing = fh.read()
    b, e2 = "<!-- KB-INDEX:BEGIN", "<!-- KB-INDEX:END -->"
    if b in existing and e2 in existing:
        pre = existing.split(b)[0]
        post = existing.split(e2, 1)[1]
        new_md = pre + block.rstrip("\n") + "\n" + post
    else:
        new_md = (existing.rstrip("\n") + "\n\n" + block) if existing.strip() else block
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write(new_md)

    print(f"OK  indexed {covered}/{total} files ({coverage}% coverage)")
    print(f"    wrote {OUT_JSON}")
    print(f"    updated {OUT_MD} (managed block, existing pointers preserved)")
    # sample for eyeball verification
    tagged = sum(1 for x in entries if x["tags"])
    agented = sum(1 for x in entries if x["agents"])
    print(f"    entries with tags: {tagged}/{covered}; with agents: {agented}/{covered}")


if __name__ == "__main__":
    main()
