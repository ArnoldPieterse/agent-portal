#!/usr/bin/env python3
"""Cycle retro auto-archiver (archivist cycle-15 goal 9).

At cycle close, generates memory/synthesis/retro-cycle-{N}.md from:
goals completed, blockers hit, time-to-completion, velocity vs prior cycle.
Appends a pointer line to memory/synthesis/INDEX.md (KB index).

Usage: python memory/archivist/retro_archiver.py --cycle N [--since DATE] [--until DATE]
Dates are YYYY-MM-DD; defaults: until = today, since = 7 days before until.
"""
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GOALS = os.path.join(ROOT, "memory", "goals")
SYNTH = os.path.join(ROOT, "memory", "synthesis")
BLOCKERS = os.path.join(ROOT, "memory", "ops", "blockers.md")


def _d(s):
    return dt.date.fromisoformat(s)


def parse_goals():
    """[(agent, title, verified_date)] for every (verified: DATE ...) line."""
    out = []
    if not os.path.isdir(GOALS):
        return out
    for fn in sorted(os.listdir(GOALS)):
        if not fn.endswith(".md") or fn == "INDEX.md":
            continue
        agent = fn[:-3]
        for line in open(os.path.join(GOALS, fn), encoding="utf-8"):
            m = re.match(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*", line)
            if not m:
                continue
            v = re.search(r"\(verified:\s*(\d{4}-\d{2}-\d{2})", line)
            if v:
                out.append((agent, m.group(1), m.group(2).strip(), _d(v.group(1))))
    return out


def parse_blockers(since, until):
    out = []
    if not os.path.exists(BLOCKERS):
        return out
    for line in open(BLOCKERS, encoding="utf-8"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if not m:
            continue
        d = _d(m.group(1))
        if since <= d <= until and "resolved" not in line.lower():
            out.append(line.strip()[:160])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", required=True)
    ap.add_argument("--since", default=None)
    ap.add_argument("--until", default=None)
    a = ap.parse_args()
    until = _d(a.until) if a.until else dt.date.today()
    since = _d(a.since) if a.since else until - dt.timedelta(days=7)
    span = (until - since).days or 1
    allg = parse_goals()
    done = [g for g in allg if since <= g[3] <= until]
    prev = [g for g in allg if since - dt.timedelta(days=span) <= g[3] < since]
    blockers = parse_blockers(since, until)[:8]
    os.makedirs(SYNTH, exist_ok=True)
    outp = os.path.join(SYNTH, "retro-cycle-%s.md" % a.cycle)
    L = ["# Cycle %s Retro (auto-archived %s)" % (a.cycle, dt.date.today().isoformat()),
         "", "Window: %s .. %s (%dd)" % (since, until, span), ""]
    L += ["## Goals Completed", ""]
    if done:
        for ag, num, title, d in done[:15]:
            L.append("- [%s] #%s %s (%s)" % (ag, num, title[:60], d))
        if len(done) > 15:
            L.append("- ... +%d more" % (len(done) - 15))
    else:
        L.append("- none in window")
    L += ["", "## Blockers Hit", ""]
    L += ["- " + b for b in blockers] if blockers else ["- none logged in window"]
    L += ["", "## Time to Completion", ""]
    if done:
        days = sorted((g[3] - since).days for g in done)
        med = days[len(days) // 2]
        L.append("- %d goals; min %dd, median %dd, max %dd (from window start)" % (len(days), days[0], med, days[-1]))
    else:
        L.append("- no completions in window")
    L += ["", "## Velocity vs Prior Cycle", ""]
    v = len(done) / span
    pv = len(prev) / span
    L.append("- this cycle: %.2f goals/day (%d)" % (v, len(done)))
    L.append("- prior window: %.2f goals/day (%d)" % (pv, len(prev)))
    L.append("- delta: %+d completions" % (len(done) - len(prev)))
    text = "\n".join(L) + "\n"
    if len(text.encode()) > 3000:
        text = "\n".join(L[:40]) + "\n- (truncated to fit 3KB)\n"
    open(outp, "w", encoding="utf-8").write(text)
    idx = os.path.join(SYNTH, "INDEX.md")
    with open(idx, "a" if os.path.exists(idx) else "w", encoding="utf-8") as f:
        if not os.path.exists(idx):
            f.write("# memory/synthesis \u2014 pointer map\n\n")
        f.write("- -> memory/synthesis/retro-cycle-%s.md   auto-retro cycle %s (%s..%s): %d completions, %d blockers\n" % (a.cycle, a.cycle, since, until, len(done), len(blockers)))
    print("wrote", outp, "(%d bytes)" % len(text.encode()))


if __name__ == "__main__":
    main()
