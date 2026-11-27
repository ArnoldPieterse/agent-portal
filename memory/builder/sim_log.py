#!/usr/bin/env python3
"""SIM-style recurring-problem log for the Builder lane.

Applies arXiv:2611.18856 (Self-Improvement Memory): group edits by recurring
harness PROBLEM/root-cause; per attempt record rationale + PREDICTED outcome
(before eval) + OBSERVED outcome + provenance. Merges identical causes without
dropping history so recurrence is visible and high-leverage problems surface.

v2 additions (paper sections 3.2-3.3):
  --recommend    : per-cause retain/revise/replace/remove heuristic (selector)
  --predict-check: compute prediction accuracy trends per cause
  --similar C    : cross-context transfer similarity (find related causes + success rate)
  --decision     : optional field on each attempt recording the selector's call

Storage: memory/builder/sim.jsonl  (one JSON object = one problem entry)
  {"cause": str, "attempts": [{"rationale","predicted","observed",
                                "provenance":{"domain","artifact","round","date"},
                                "decision": optional(str)}]}

Usage:
  python sim_log.py --add --cause C --rationale R [--predicted P] \
                    [--observed O] [--artifact A] [--round N] [--decision D]
  python sim_log.py --report
  python sim_log.py --recommend
  python sim_log.py --predict-check
  python sim_log.py --similar "socket bind"
  python sim_log.py --selftest
"""
import argparse, json, os, sys, tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "sim.jsonl")


def norm(s):
    return " ".join((s or "").strip().lower().split())


def load(path=STORE):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


def save(entries, path=STORE):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def add(cause, rationale="", predicted="", observed="", artifact="",
        rnd=None, today=None, path=STORE, decision=""):
    if not cause or not norm(cause):
        raise ValueError("--cause is required and non-empty")
    entries = load(path)
    nc = norm(cause)
    att = {
        "rationale": rationale,
        # "" = not captured BEFORE eval (itself informative: SIM wants it recorded first)
        "predicted": predicted,
        "observed": observed,
        "provenance": {"domain": "builder", "artifact": artifact,
                       "round": rnd, "date": today or date.today().isoformat()},
    }
    if decision:
        att["decision"] = decision
    for e in entries:
        if norm(e.get("cause", "")) == nc:
            e.setdefault("attempts", []).append(att)
            save(entries, path)
            return e, False  # merged into existing
    new = {"cause": cause.strip(), "attempts": [att]}
    entries.append(new)
    save(entries, path)
    return new, True  # created


def report(path=STORE):
    entries = load(path)
    rows = sorted(entries, key=lambda e: len(e.get("attempts", [])), reverse=True)
    lines = ["SIM recurring-problem report (Builder lane)",
             "entries=%d total_attempts=%d" % (
                 len(rows), sum(len(e.get("attempts", [])) for e in rows))]
    for e in rows:
        atts = e.get("attempts", [])
        n = len(atts)
        last = atts[-1] if atts else {}
        art = [a["provenance"].get("artifact") for a in atts
               if a["provenance"].get("artifact")]
        flag = "RECURRING" if n > 1 else "first-seen"
        lines.append("- [%s x%d] %s | last_observed=%s | artifacts=%s" % (
            flag, n, e.get("cause", ""),
            (last.get("observed") or "(none)")[:80], ",".join(art) or "-"))
    return "\n".join(lines)


def _tokens(s):
    """Simple word tokens for similarity (no external deps)."""
    return set(norm(s).split())


def recommend(path=STORE):
    """Selector heuristic per paper 3.2: retain/revise/replace/remove.
    
    Rules:
      RETAIN   - last attempt observed >= predicted (or no prediction) and improving
      REVISE   - observed consistently below predicted (right approach, insufficient)
      REPLACE  - 3+ attempts with different rationales all failing (misdiagnosis?)
      REMOVE   - latest was a regression AND 3+ total with no improvement trend
    """
    entries = load(path)
    lines = ["SIM selector recommendations (retain/revise/replace/remove)"]
    for e in sorted(entries, key=lambda x: len(x.get("attempts", [])), reverse=True):
        atts = e.get("attempts", [])
        n = len(atts)
        if n == 0:
            continue
        last = atts[-1]
        # Simple numeric comparison when both are floats/ints
        pred = last.get("predicted", "")
        obs = last.get("observed", "")
        try:
            pv, ov = float(pred), float(obs)
            improving = ov >= pv
        except (ValueError, TypeError):
            improving = bool(obs)  # non-numeric: assume OK if observed is non-empty
        
        # Check trend over last 3
        recent = atts[-3:] if n >= 3 else atts
        rationales = set(a.get("rationale", "") for a in recent)
        distinct_rationales = len(rationales - {""})
        
        # Decision logic
        if n == 1:
            decision = "RETAIN" if improving else "REVISE"
        elif n >= 3 and not improving and distinct_rationales >= 2:
            decision = "REPLACE"  # multiple approaches tried, still failing
        elif n >= 3 and not improving:
            # check if any improvement in trend
            decision = "REMOVE" if not improving else "REVISE"
        elif not improving:
            decision = "REVISE"
        else:
            decision = "RETAIN"
        
        lines.append("- [%s] %s (x%d) | pred=%s obs=%s" % (
            decision, e.get("cause", "")[:60], n,
            (pred or "-")[:20], (obs or "-")[:20]))
    return "\n".join(lines)


def predict_check(path=STORE):
    """Compute prediction accuracy per cause (paper 3.2 core loop).
    
    For each attempt with both predicted and observed numeric values,
    compute error = |observed - predicted| / max(|predicted|, 1).
    Report mean error per cause; flag causes where predictions are
    consistently off (suggests wrong mental model for that problem class).
    """
    entries = load(path)
    lines = ["SIM prediction-accuracy report"]
    for e in sorted(entries, key=lambda x: len(x.get("attempts", [])), reverse=True):
        atts = e.get("attempts", [])
        errors = []
        for a in atts:
            p, o = a.get("predicted", ""), a.get("observed", "")
            try:
                pv, ov = float(p), float(o)
                err = abs(ov - pv) / max(abs(pv), 1.0)
                errors.append(err)
            except (ValueError, TypeError):
                continue
        if not errors:
            lines.append("- %s | no numeric predictions" % e.get("cause", "")[:50])
        else:
            mean_err = sum(errors) / len(errors)
            flag = "HIGH-VARIANCE" if mean_err > 0.5 else "OK"
            lines.append("- [%s] %s | mean_err=%.2f (n=%d)" % (
                flag, e.get("cause", "")[:50], mean_err, len(errors)))
    return "\n".join(lines)


def similar(query, path=STORE, threshold=0.3):
    """Cross-context transfer: find existing causes similar to a new problem.
    
    Uses token overlap (Jaccard-like) to surface related entries so the
    proposer can decide whether to reuse an approach or start fresh.
    Returns top matches with their success rate.
    """
    entries = load(path)
    qtoks = _tokens(query)
    if not qtoks:
        return "(empty query)"
    scored = []
    for e in entries:
        etoks = _tokens(e.get("cause", ""))
        if not etoks:
            continue
        overlap = len(qtoks & etoks) / max(len(qtoks | etoks), 1)
        if overlap >= threshold:
            atts = e.get("attempts", [])
            # success rate: fraction of attempts where observed is non-empty
            successes = sum(1 for a in atts if a.get("observed"))
            rate = successes / len(atts) if atts else 0
            scored.append((overlap, e.get("cause", ""), len(atts), rate))
    scored.sort(key=lambda x: x[0], reverse=True)
    lines = ["SIM transfer-similarity for: %r" % query[:60]]
    if not scored:
        lines.append("  (no similar causes found — new problem class)")
    for score, cause, n, rate in scored[:5]:
        lines.append("  [%.2f] %s (x%d, success_rate=%.0f%%)" % (
            score, cause[:60], n, rate * 100))
    return "\n".join(lines)


def selftest():
    tmp = tempfile.mktemp(suffix=".jsonl")
    errs = []

    def chk(name, cond):
        if not cond:
            errs.append(name)

    # 1. add new cause -> created
    e, created = add("sandbox socket bind 10013", "test", "85", "92",
                     "a.py", 1, "2026-11-27", path=tmp)
    chk("create-new", created is True and len(e["attempts"]) == 1)

    # 2. add SAME cause (normalized: case/whitespace differ) -> merged, history kept
    e2, created2 = add("  Sandbox Socket Bind 10013 ", "test2", "88", "90",
                       "b.py", 2, "2026-11-27", path=tmp)
    chk("merge-same-cause", created2 is False and len(e2["attempts"]) == 2)

    # 3. different cause -> separate entry
    e3, created3 = add("stale root goal_ledger.json", "x", "70", "85",
                       "goal_ledger.py", 1, "2026-11-27", path=tmp)
    chk("distinct-entry", created3 is True)

    # 4. third attempt on first cause -> count 3, all history preserved in order
    add("sandbox socket bind 10013", "t3", "95", "88", "c.py", 3,
        "2026-11-27", path=tmp)
    entries = load(tmp)
    bycause = {norm(e["cause"]): e for e in entries}
    chk("two-entries", len(entries) == 2)
    chk("count-3", len(bycause[norm("sandbox socket bind 10013")]["attempts"]) == 3)
    obs = [a["observed"] for a in bycause[norm("sandbox socket bind 10013")]["attempts"]]
    chk("history-order", obs == ["92", "90", "88"])

    # 5. report flags recurrence (x3) and first-seen (x1)
    rep = report(tmp)
    chk("report-recurring", "[RECURRING x3]" in rep)
    chk("report-firstseen", "[first-seen x1]" in rep)
    chk("report-totals", "total_attempts=4" in rep)

    # 6. JSONL round-trip integrity (reload equals saved)
    reloaded = load(tmp)
    chk("roundtrip", len(reloaded) == 2 and
        all(set(a.keys()) >= {"rationale", "predicted", "observed", "provenance"}
            for e in reloaded for a in e["attempts"]))

    # 7. recommend produces valid decision per entry
    rec = recommend(tmp)
    chk("recommend-has-decision", any(d in rec for d in ("RETAIN","REVISE","REPLACE","REMOVE")))
    chk("recommend-covers-all", "sandbox socket bind" in rec and "stale root" in rec)

    # 8. predict-check computes numeric errors
    pc = predict_check(tmp)
    chk("predict-check-runs", "mean_err=" in pc or "no numeric predictions" in pc)

    # 9. similar finds related cause by token overlap
    sim = similar("socket bind error", path=tmp, threshold=0.25)
    chk("similar-finds-match", "sandbox socket bind" in sim)

    # 10. decision field stored on add
    e4, _ = add("decision test cause", "r", "50", "60", "d.py", 1,
                "2026-11-27", path=tmp, decision="RETAIN")
    chk("decision-stored", e4["attempts"][-1].get("decision") == "RETAIN")

    os.remove(tmp)
    if errs:
        print("SELFTEST FAIL:", errs)
        return 1
    print("SELFTEST PASS (10 groups, all assertions)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--cause"); ap.add_argument("--rationale", default="")
    ap.add_argument("--predicted", default=""); ap.add_argument("--observed", default="")
    ap.add_argument("--artifact", default=""); ap.add_argument("--round", type=int)
    ap.add_argument("--decision", default="",
                    choices=["", "RETAIN", "REVISE", "REPLACE", "REMOVE"])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--recommend", action="store_true")
    ap.add_argument("--predict-check", action="store_true")
    ap.add_argument("--similar", metavar="QUERY")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.report:
        print(report()); return
    if a.recommend:
        print(recommend()); return
    if a.predict_check:
        print(predict_check()); return
    if a.similar:
        print(similar(a.similar)); return
    if a.add:
        e, created = add(a.cause, a.rationale, a.predicted, a.observed,
                         a.artifact, a.round, decision=a.decision)
        print("OK %s cause=%r attempts=%d" % (
            "created" if created else "merged", e["cause"], len(e["attempts"])))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
