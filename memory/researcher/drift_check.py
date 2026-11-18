# Terminology Drift Monitor (Researcher cycle-5 goal 8)
# Track how key fleet terms are used across goal files over time (per dated snapshot),
# and flag any term whose relative usage shifts >20% from the baseline snapshot.
#
# Usage:
#   python memory/researcher/drift_check.py [--threshold 0.2] [--terms loop,agent,...]
# Writes a JSON report to memory/researcher/drift-report-<date>.json and prints a table.
import os, re, sys, json, glob
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
GOALS_DIR = os.path.join(ROOT, "memory", "goals")
ARCHIVE_DIR = os.path.join(GOALS_DIR, "archive")

KEY_TERMS = ["loop", "agent", "task", "module", "reply", "record"]
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _count_terms(text, terms):
    """Whole-word counts (case-insensitive) for each term in KEY_TERMS."""
    low = text.lower()
    total_words = len(re.findall(r"[a-z0-9]+", low)) or 1
    counts = {}
    for t in terms:
        n = len(re.findall(r"\b%s\b" % re.escape(t), low))
        counts[t] = {"count": n, "per_k": round(1000.0 * n / total_words, 3)}
    return counts, total_words


def _snapshot_files():
    """Map date -> list of goal .md files for that snapshot.
    Live files (no date) are grouped under today as the 'current' snapshot."""
    snaps = {}
    # archive: per-agent dated files like researcher-2026-11-18.md
    for f in glob.glob(os.path.join(ARCHIVE_DIR, "*.md")):
        base = os.path.basename(f)
        m = DATE_RE.search(base)
        if not m:
            continue  # skip INDEX/README/SUPERSEDED (no date or already superseded)
        if "SUPERSEDED" in base.upper():
            continue
        snaps.setdefault(m.group(1), []).append(f)
    # live files = current snapshot
    today = date.today().isoformat()
    live = [os.path.join(GOALS_DIR, a + ".md") for a in
            ("orchestrator", "researcher", "builder", "verifier", "designer",
             "archivist", "scribe", "mechanic") if os.path.exists(os.path.join(GOALS_DIR, a + ".md"))]
    if live:
        snaps.setdefault(today, []).extend(live)
    return snaps


def _snapshot_text(files):
    parts = []
    for f in files:
        try:
            parts.append(open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            pass
    return "\n".join(parts)


def analyze(threshold=0.20, terms=None):
    terms = terms or KEY_TERMS
    snaps = _snapshot_files()
    if len(snaps) < 2:
        return {"ok": False, "error": "need >=2 dated snapshots; found %d" % len(snaps)}
    dates = sorted(snaps.keys())
    per_date = {}
    for d in dates:
        text = _snapshot_text(snaps[d])
        counts, total_words = _count_terms(text, terms)
        per_date[d] = {"files": len(snaps[d]), "total_words": total_words, "terms": counts}

    base_d, cur_d = dates[0], dates[-1]
    base_t, cur_t = per_date[base_d]["terms"], per_date[cur_d]["terms"]
    drift = []
    for t in terms:
        b, c = base_t[t]["per_k"], cur_t[t]["per_k"]
        denom = max(b, 1e-9)
        rel = (c - b) / denom if b > 0 else (1.0 if c > 0 else 0.0)
        drift.append({"term": t, "baseline_per_k": b, "current_per_k": c,
                      "rel_change": round(rel, 3),
                      "flagged": abs(rel) > threshold})
    flagged = [x for x in drift if x["flagged"]]
    return {"ok": True, "baseline": base_d, "current": cur_d,
            "threshold": threshold, "snapshots": dates,
            "per_snapshot_words": {d: per_date[d]["total_words"] for d in dates},
            "drift": drift, "flagged_terms": [x["term"] for x in flagged],
            "note": ("%d term(s) shifted >%.0f%% from baseline" % (len(flagged), threshold * 100)
                     if flagged else "no term shifted beyond threshold")}


if __name__ == "__main__":
    args = sys.argv[1:]
    thr, terms = 0.20, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--threshold" and i + 1 < len(args):
            thr = float(args[i + 1]); i += 2; continue
        if a == "--terms" and i + 1 < len(args):
            terms = [t.strip() for t in args[i + 1].split(",") if t.strip()]; i += 2; continue
        i += 1
    res = analyze(thr, terms)
    out_path = os.path.join(HERE, "drift-report-%s.json" % date.today().isoformat())
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: res.get(k) for k in
                      ("ok", "baseline", "current", "threshold", "snapshots",
                       "flagged_terms", "note")}, indent=2))
    if res.get("ok"):
        print("\n%-8s %10s %10s %10s  %s" % ("term", "base/1k", "cur/1k", "relΔ", "flag"))
        for x in res["drift"]:
            print("%-8s %10.3f %10.3f %+9.1f%%  %s" % (
                x["term"], x["baseline_per_k"], x["current_per_k"],
                x["rel_change"] * 100, "<== DRIFT" if x["flagged"] else ""))
        print("\nreport -> %s" % os.path.relpath(out_path, ROOT))
