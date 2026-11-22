#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""auto_abstract.py - Archivist Goal (cycle-10): auto-abstraction pipeline.
Detects recently changed .md files under memory/ (git diff when available,
mtime fallback) and writes a sidecar abstract (first paragraph + headings)
so the index stays current without manual summaries.

Usage:
  python auto_abstract.py [--hours N]   # default: last 24h; --force to do all
"""
import os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MEMORY = os.path.join(ROOT, "memory")
HEADING_RE = re.compile(r"^#{1,3}\s+(.*)$")

def recent_files(hours):
    try:
        out = subprocess.run(["git", "-C", ROOT, "diff", "--name-only",
                              f"--since={hours} hours ago", "HEAD~7"],
                             capture_output=True, text=True, timeout=30).stdout
        files = [l.strip() for l in out.splitlines()
                 if l.strip().endswith(".md") and l.strip().startswith("memory/")]
        if files:
            return files, "git"
    except Exception:
        pass
    cutoff = time.time() - hours * 3600
    files = []
    for dirpath, _, filenames in os.walk(MEMORY):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if fn.endswith(".md") and os.path.getmtime(p) >= cutoff:
                files.append(os.path.relpath(p, ROOT).replace("\\", "/"))
    return files, "mtime"

def abstract_for(path):
    text = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    headings = [HEADING_RE.match(l).group(1).strip() for l in lines if HEADING_RE.match(l)][:8]
    para = ""
    for l in lines:
        s = l.strip()
        if s and not s.startswith("#") and not s.startswith("-") and len(s) > 40:
            para = s[:220]
            break
    return {"path": path, "headings": headings, "lead": para,
            "chars": len(text), "abstracted": time.strftime("%Y-%m-%d %H:%M:%S")}

def main():
    hours = 24
    if "--hours" in sys.argv:
        hours = int(sys.argv[sys.argv.index("--hours") + 1])
    force = "--force" in sys.argv
    files, source = recent_files(hours)
    if force:
        files = [os.path.relpath(os.path.join(dp, fn), ROOT).replace("\\", "/")
                 for dp, _, fns in os.walk(MEMORY) for fn in fns if fn.endswith(".md")]
        source = "force"
    out_dir = os.path.join(HERE, "abstracts")
    os.makedirs(out_dir, exist_ok=True)
    done = 0
    for rel in files:
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        a = abstract_for(rel)
        sidecar = os.path.join(out_dir, rel.replace("/", "__") + ".abstract.json")
        json_exists = os.path.exists(sidecar)
        import json as _j
        _j.dump(a, open(sidecar, "w", encoding="utf-8"), indent=1)
        done += 0 if json_exists else 1
    print(f"source={source} candidates={len(files)} new_abstracts={done}")

if __name__ == "__main__":
    main()
