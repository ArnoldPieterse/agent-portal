#!/usr/bin/env python3
"""
cycle_quality.py - Verifier goal #10: Cycle Quality Report (cycle-8)

End-of-cycle auto-generated report. Reads LOCAL artifacts only (no network / :8099):
  goals, evidence-quality, security-audit, slo-report, perf-baseline, evidence-xref, git log.
Output: memory/verifier/cycle-N-quality-report.md
Honesty rule: a perf baseline with no valid samples is reported DEGRADED, never a PASS.

Usage:
    python memory/verifier/cycle_quality.py                 # auto-detect cycle from goal headers
    python memory/verifier/cycle_quality.py --cycle 8       # force cycle number
"""
import argparse, json, os, re, sys, subprocess, datetime, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)

AGENTS = ["archivist","builder","designer","mechanic","orchestrator","researcher","scribe","verifier"]
CLOSED_RE = re.compile(r"\((verified|validated)\s*:", re.I)

# ---- goals ---------------------------------------------------------------
def parse_goals():
    """Return {agent: (total, closed)} by counting numbered goals and closed markers."""
    out = {}
    for a in AGENTS:
        fp = p("memory", "goals", a + ".md")
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding="utf-8", errors="replace").read()
        nums = re.findall(r"(?m)^\s*(\d{1,2})\.\s+\*\*", txt)
        total = max(int(n) for n in nums) if nums else 0
        blocks = re.split(r"(?m)^\s*(?:\d{1,2}\.\s+\*\*)", txt)
        closed = 0
        for i in range(1, len(blocks), 2):
            if CLOSED_RE.search(blocks[i + 1]):
                closed += 1
        out[a] = (total, closed)
    return out

def detect_cycle():
    for a in AGENTS:
        fp = p("memory", "goals", a + ".md")
        if os.path.exists(fp):
            m = re.search(r"cycle[- ]?(\d+)", open(fp, encoding="utf-8", errors="replace").read(400), re.I)
            if m:
                return int(m.group(1))
    return None

# ---- evidence quality ----------------------------------------------------
def parse_evidence_quality():
    files = sorted(glob.glob(p("memory", "ops", "evidence-quality-*.md")))
    if not files:
        return None, None
    fp = files[-1]
    txt = open(fp, encoding="utf-8", errors="replace").read()
    def grab(label):
        m = re.search(re.escape(label) + r"\s*\|\s*([^|]+)\|", txt)
        return m.group(1).strip() if m else None
    def num(s):
        try: return int(re.sub(r"[^0-9]", "", s or ""))
        except Exception: return None
    return {
        "total": (lambda s: int(s) if s and s.isdigit() else None)(grab("Total leaves scored")),
        "flagged": grab("Flagged (<3 on any axis)"),
        "high": grab("High quality (composite >=4.0)"),
        "low": grab("Low quality (composite <2.5)"),
        "avg_spec": grab("Avg specificity"),
        "avg_repro": grab("Avg reproducibility"),
        "avg_curr": grab("Avg currency"),
    }, fp

# ---- security ------------------------------------------------------------
def parse_security():
    files = sorted(glob.glob(p("memory", "verifier", "security-audit-*.md")))
    if not files:
        return None, None
    fp = files[-1]
    txt = open(fp, encoding="utf-8", errors="replace").read()
    # Pattern 1: severity as a standalone bold cell in a table row: | **HIGH** |
    # Pattern 2: severity as plain text cell: | HIGH |
    # Pattern 3: section header: ## HIGH
    def cellcount(s):
        # severity can appear in any column of a table row: | ... | **HIGH** | ...
        c = len(re.findall(r"(?m)^\|.*\*\*" + s + r"\*\*.*\|", txt))
        if c == 0:
            c = len(re.findall(r"(?m)^\|\s*" + s + r"\s*\|", txt))
        if c == 0:
            c = len(re.findall(r"(?im)^#{2,4}\s*" + s + r"\b", txt))
        return c
    sev = {s: cellcount(s) for s in ["CRITICAL","HIGH","MEDIUM","LOW"]}
    return sev, fp

# ---- SLO -----------------------------------------------------------------
def parse_slo():
    files = sorted(glob.glob(p("memory", "verifier", "slo-report-*.md")))
    res = {"latest": None, "verdict": None, "endpoints_ok": 0, "endpoints_total": 0, "alerts": 0}
    if files:
        txt = open(files[-1], encoding="utf-8", errors="replace").read()
        res["latest"] = os.path.basename(files[-1])
        m = re.search(r"\*\*Verdict:\s*(PASS|FAIL|DEGRADED)\*\*", txt)
        if m: res["verdict"] = m.group(1)
        rows = [r for r in re.findall(r"(?m)^/api/.+$", txt)]
        ok = [r for r in rows if "OK" in r]
        res["endpoints_ok"] = len(ok)
        res["endpoints_total"] = len(rows)
    afp = p("memory", "ops", "slo-alerts.jsonl")
    if os.path.exists(afp):
        res["alerts"] = sum(1 for ln in open(afp, encoding="utf-8", errors="replace") if ln.strip())
    return res

# ---- perf ----------------------------------------------------------------
def parse_perf():
    fp = p("memory", "verifier", "perf-baseline.json")
    if not os.path.exists(fp):
        return {"status": "ABSENT", "detail": "no perf-baseline.json", "sampled": 0, "total": 0}
    try:
        d = json.load(open(fp, encoding="utf-8"))
    except Exception as e:
        return {"status": "UNPARSEABLE", "detail": str(e), "sampled": 0, "total": 0}
    eps = d.get("endpoints", {})
    total = len(eps)
    sampled = sum(1 for v in eps.values() if isinstance(v, dict) and (v.get("p50_ms") is not None or v.get("p95_ms") is not None))
    if total == 0:
        return {"status": "ABSENT", "detail": "empty endpoints", "sampled": 0, "total": 0}
    if sampled == 0:
        # all-null = captured behind egress wall (WinError 10013) -> NOT a valid baseline
        return {"status": "DEGRADED", "detail": "all endpoints null (egress-wall capture, no live samples)",
                "sampled": 0, "total": total, "captured_at": d.get("captured_at")}
    p95 = [v["p95_ms"] for v in eps.values() if isinstance(v, dict) and v.get("p95_ms") is not None]
    return {"status": "OK", "detail": "%d/%d endpoints sampled" % (sampled, total), "sampled": sampled,
            "total": total, "p95_max_ms": max(p95), "captured_at": d.get("captured_at")}

# ---- evidence xref -------------------------------------------------------
def parse_xref():
    files = sorted(glob.glob(p("memory", "verifier", "evidence-xref-report-*.md")))
    if not files:
        return None
    txt = open(files[-1], encoding="utf-8", errors="replace").read()
    # Format: "Dangling (broken) references: 0" or "N dangling"
    m = re.search(r"[Dd]angling[^:]*:\s*(\d+)", txt)
    if not m:
        m = re.search(r"(\d+)\s+dangling", txt, re.I)
    return {"file": os.path.basename(files[-1]), "dangling": int(m.group(1)) if m else None}

# ---- git -----------------------------------------------------------------
def git_activity(days=14):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "--since=%d days ago" % days,
                              "--pretty=%h %ad %s", "--date=short"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        lines = [l for l in out.splitlines() if l.strip()]
        return {"commits": len(lines), "recent": lines[:8]}
    except Exception as e:
        return {"commits": None, "recent": [], "error": str(e)}

# ---- report --------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, default=None)
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    cycle = args.cycle or detect_cycle() or 0
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    goals = parse_goals()
    tot = sum(v[0] for v in goals.values()); clo = sum(v[1] for v in goals.values())
    rate = (100.0 * clo / tot) if tot else 0.0
    evq, evq_src = parse_evidence_quality()
    sec, sec_src = parse_security()
    slo = parse_slo()
    perf = parse_perf()
    xref = parse_xref()
    git = git_activity(args.days)

    NL = chr(10)
    L = []
    L.append("# Cycle %d Quality Report" % cycle)
    L.append("")
    L.append("Generated: %s by `memory/verifier/cycle_quality.py` (local artifacts only; no :8099 egress)." % now)
    L.append("")
    # 1 goals
    L.append("## 1. Goals Completed + Verification Pass Rate")
    L.append("")
    L.append("| Agent | Closed | Total | % |")
    L.append("|-------|-------|-------|---|")
    for a in AGENTS:
        if a not in goals: continue
        t, c = goals[a]
        L.append("| %s | %d | %d | %s |" % (a, c, t, ("%.0f%%" % (100.0*c/t)) if t else "-"))
    L.append("| **Fleet** | **%d** | **%d** | **%.0f%%** |" % (clo, tot, rate))
    L.append("")
    # 2 evidence quality
    L.append("## 2. Evidence Quality Scores")
    L.append("")
    if evq:
        L.append("Source: `%s` (rubric: specificity/reproducibility/currency, 1-5)." % os.path.basename(evq_src))
        L.append("")
        L.append("- Leaves scored: **%s** | flagged (<3 any axis): %s" % (evq["total"], evq["flagged"]))
        L.append("- High (>=4.0): %s | Low (<2.5): %s" % (evq["high"], evq["low"]))
        L.append("- Averages: spec=%s repro=%s curr=%s" % (evq["avg_spec"], evq["avg_repro"], evq["avg_curr"]))
    else:
        L.append("No evidence-quality report found.")
    L.append("")
    # 3 SLO
    L.append("## 3. SLO Compliance")
    L.append("")
    if slo["latest"]:
        L.append("Latest report: `%s` | Verdict: **%s** | endpoints OK %d/%d | alerts logged: %d"
                 % (slo["latest"], slo["verdict"], slo["endpoints_ok"], slo["endpoints_total"], slo["alerts"]))
    else:
        L.append("No SLO report found.")
    L.append("")
    # 4 security
    L.append("## 4. Security Findings")
    L.append("")
    if sec is not None:
        L.append("Source: `%s`." % os.path.basename(sec_src))
        L.append("")
        L.append("| Severity | Count |")
        L.append("|----------|-------|")
        for s in ["CRITICAL","HIGH","MEDIUM","LOW"]:
            L.append("| %s | %d |" % (s, sec.get(s,0)))
    else:
        L.append("No security audit found.")
    L.append("")
    # 5 performance (honesty rule)
    L.append("## 5. Performance Trends")
    L.append("")
    if perf["status"] == "OK":
        L.append("Baseline OK (%s): %s, max p95 = %s ms." % (perf.get("captured_at"), perf["detail"], perf.get("p95_max_ms")))
    elif perf["status"] == "DEGRADED":
        L.append("**DEGRADED** (captured %s): %s. No live samples available from this seat (:8099 egress wall) - reported as NOT PASS, not a regression." % (perf.get("captured_at"), perf["detail"]))
    else:
        L.append("Baseline %s: %s" % (perf["status"], perf["detail"]))
    L.append("")
    # 6 evidence integrity
    L.append("## 6. Evidence Integrity (cross-reference)")
    L.append("")
    if xref:
        L.append("Source: `%s` | dangling refs: **%s**" % (xref["file"], xref["dangling"]))
    else:
        L.append("No evidence-xref report found.")
    L.append("")
    # 7 git activity
    L.append("## 7. Git Activity (last %d days)" % args.days)
    L.append("")
    if git["commits"] is None:
        L.append("git unavailable: %s" % git.get("error",""))
    else:
        L.append("Commits: **%d**" % git["commits"])
        for c in git["recent"]:
            L.append("- `%s` %s" % (c[:7], c[8:]))
    L.append("")
    # 8 summary
    L.append("## 8. Cycle Summary / Verdict")
    L.append("")
    sec_total = sum(sec.values()) if sec else 0
    bits = ["goals %d/%d (%.0f%%)" % (clo, tot, rate), "SLO=%s" % (slo["verdict"] or "n/a"),
            "security findings=%d" % sec_total, "perf=%s" % perf["status"],
            "dangling refs=%s" % (xref["dangling"] if xref else "n/a")]
    L.append(" ".join(bits))
    L.append("")

    out = p("memory", "verifier", "cycle-%d-quality-report.md" % cycle)
    open(out, "w", encoding="utf-8", newline="").write(NL.join(L) + NL)
    print("WROTE memory/verifier/cycle-%d-quality-report.md (%d lines)" % (cycle, len(L)))
    summ = {"cycle": cycle, "goals_closed": clo, "goals_total": tot, "pass_rate_pct": round(rate,1),
            "evidence_quality_src": os.path.basename(evq_src) if evq_src else None,
            "slo_verdict": slo["verdict"], "security_findings": sec_total,
            "perf_status": perf["status"], "dangling_refs": xref["dangling"] if xref else None,
            "git_commits_14d": git["commits"]}
    print(json.dumps(summ))
    return 0

if __name__ == "__main__":
    sys.exit(main())
