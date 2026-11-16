#!/usr/bin/env python
# Researcher goal #10 - reproducible evidence-quality trend (weekly report generator).
#
# Metric (matches weekly report 1/2): across every agent's goal file, for each
# `(verified: ...)` closure marker, does at least one cited evidence file
# (.md/.py/.json) actually exist on disk? Fleet real-evidence rate =
# markers-with-existing-leaf / total verified markers. Data only, no prose.
#
# Usage:  python memory/researcher/evidence_quality_trend.py [--min-markers 20]
#         prints a markdown table row (drop into report N) + per-agent breakdown.
# Exit 0 always; --min-markers sets the stability threshold for the verdict line.

import os, re, sys, glob, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GOALS = os.path.join(ROOT, "memory", "goals")
# index every real file by basename so cited leaves resolve regardless of dir
def _index_files():
    idx = {}
    for pat in ("memory/**/*.md", "memory/**/*.py", "memory/**/*.json",
                "*.md", "*.py", "*.json"):
        for f in glob.glob(os.path.join(ROOT, pat), recursive=True):
            if os.path.isfile(f):
                idx.setdefault(os.path.basename(f).lower(), []).append(f)
    return idx

FILE_TOK = re.compile(r"([\w./-]+\.(?:md|py|json))", re.I)
MARKER   = re.compile(r"\(verified:\s*(.+?)\)\s*$", re.I | re.M)

def main():
    minm = 20
    if "--min-markers" in sys.argv:
        i = sys.argv.index("--min-markers"); minm = int(sys.argv[i+1])
    idx = _index_files()
    per_agent, tot_m, tot_ok = {}, 0, 0
    for gf in sorted(glob.glob(os.path.join(GOALS, "*.md"))):
        agent = os.path.splitext(os.path.basename(gf))[0]
        txt = open(gf, encoding="utf-8", errors="replace").read()
        marks = MARKER.findall(txt)
        ok = 0
        for m in marks:
            tot_m += 1
            toks = FILE_TOK.findall(m)
            if any(os.path.basename(t).lower() in idx for t in toks):
                ok += 1; tot_ok += 1
        per_agent[agent] = (len(marks), ok)
    rate = (100.0 * tot_ok / tot_m) if tot_m else 0.0
    today = datetime.date.today().isoformat()
    verdict = "STABLE (n>={})".format(minm) if tot_m >= minm else "n={} (<{} , not yet stable)".format(tot_m, minm)
    print("| {} | fleet-wide cycle-2 closures | {} | {}/{} verified markers have a cited leaf on disk | evidence_quality_trend.py |".format(
        today, verdict, round(rate), tot_ok, tot_m))
    print()
    for a in sorted(per_agent):
        m, ok = per_agent[a]
        r = (100.0 * ok / m) if m else 0.0
        print("{:<14} {}/{} verified -> {:.0f}%".format(a, ok, m, r))
    print()
    print("TOTAL: {}/{} = {:.0f}%  (threshold for report-2 stable rate: {} markers)".format(tot_ok, tot_m, round(rate), minm))

if __name__ == "__main__":
    main()