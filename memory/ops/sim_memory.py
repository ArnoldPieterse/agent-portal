#!/usr/bin/env python
"""SIM-style ops memory (Self-Improvement Memory, arXiv:2611.18856).

Groups harness/ops edits by recurring root-cause and records each attempt's
rationale, PREDICTED outcome, OBSERVED outcome, and provenance, so the next
optimization pass can decide retain / revise / replace / remove instead of
re-learning from scratch or repeating a fix that already regressed.

Storage: memory/ops/sim_entries.json (single small file, stdlib only).

Usage:
  add   --root-cause "..." --rationale "..." --predicted "..." \
        --observed "..." --artifact "rel/path" --agent X [--outcome improved|regressed|neutral] [--date YYYY-MM-DD]
  report                 # recurring problems, regressions, reuse hints
  selftest               # in-memory round-trip assertions
"""
import argparse, json, sys, hashlib, datetime, re
from pathlib import Path

STORE = "memory/ops/sim_entries.json"

def norm(text):
    t = (text or "").strip().lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def load():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"entries": []}
    except json.JSONDecodeError:
        print("ERROR: %s is corrupt JSON" % STORE, file=sys.stderr); sys.exit(2)

def save(data):
    Path(STORE).parent.mkdir(parents=True, exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False); f.write("\n")

def add(args):
    data = load()
    key = norm(args.root_cause)
    date = args.date or datetime.date.today().isoformat()
    attempt = {
        "rationale": args.rationale,
        "predicted": args.predicted,
        "observed": args.observed,
        "outcome": args.outcome,
        "artifact": args.artifact,
        "agent": args.agent,
        "date": date,
        "context": getattr(args, 'context', None),  # e.g. "cycle=77;seats_down=Mechanic"
    }
    for e in data["entries"]:
        if norm(e["root_cause"]) == key:
            e["attempts"].append(attempt)
            e["last_updated"] = date
            merged = True
            break
    else:
        data["entries"].append({
            "root_cause": args.root_cause.strip(),
            "key": hashlib.sha1(key.encode()).hexdigest()[:12],
            "created": date, "last_updated": date,
            "attempts": [attempt],
        })
        merged = False
    save(data)
    print(("merged into existing entry" if merged else "new entry created") +
          " | root_cause=%r attempts_total=%d" % (args.root_cause, len([a for e in data['entries'] for a in e['attempts']])))

def classify(e):
    """Return (decision, confidence) using the paper's 4-way taxonomy.

    Decision: RETAIN | REVISE | REPLACE | REMOVE
      RETAIN  - fix worked and context is stable; reuse as-is
      REVISE  - fix partially worked or context changed; adjust before reuse
      REPLACE - repeated failures; try a fundamentally different approach
      REMOVE  - last attempt regressed with no prior success; drop the mechanism

    Confidence: 0.0-1.0 based on prediction accuracy (predicted matched observed).
    """
    atts = e["attempts"]
    if not atts: return ("no-data", 0.0)
    last = atts[-1]
    improved  = [a for a in atts if a.get("outcome") == "improved"]
    regressed = [a for a in atts if a.get("outcome") == "regressed"]
    neutral   = [a for a in atts if a.get("outcome") == "neutral"]

    # Prediction accuracy: did the predicted outcome match actual?
    # (improved/neutral count as 'hit' when predicted was positive; regressed = miss)
    hits = sum(1 for a in atts if (a.get("outcome") != "regressed" and a.get("predicted")))
    total_with_pred = sum(1 for a in atts if a.get("predicted"))
    acc = hits / total_with_pred if total_with_pred else 0.5

    # Context shift detection: compare last attempt context vs first
    ctx_shift = False
    if len(atts) >= 2 and atts[0].get("context") and atts[-1].get("context"):
        ctx_shift = atts[0]["context"] != atts[-1]["context"]

    # 4-way decision
    if regressed and not improved:
        decision = "REMOVE" if len(atts) == 1 else "REPLACE"
    elif regressed and improved:
        decision = "REVISE"  # mixed results -> adjust
    elif improved:
        decision = "RETAIN" if not ctx_shift else "REVISE"  # context changed -> re-verify
    else:
        decision = "REVISE" if len(atts) >= 2 else "REPLACE"

    # Boost confidence if context stable and consistent outcomes
    if ctx_shift: acc *= 0.7  # discount for context drift
    return (decision, round(acc, 2))

def report(_args):
    data = load()
    entries = sorted(data["entries"], key=lambda e: -len(e["attempts"]))
    if not entries:
        print("SIM memory empty (%s). Use 'add' to record an ops edit." % STORE); return
    print("=== SIM ops memory report ===  (%d root-cause problem(s), %d total attempt(s))\n" %
          (len(entries), sum(len(e["attempts"]) for e in entries)))
    for e in entries:
        decision, conf = classify(e)
        flag = "RECURRING" if len(e["attempts"]) >= 2 else "single"
        print("[%s @%.0f%%] %s  (attempts=%d, %s)" % (decision, conf*100, e["root_cause"], len(e["attempts"]), flag))
        for a in e["attempts"]:
            ctx = " [%s]" % a["context"] if a.get("context") else ""
            print("    %s | out=%-9s%s | pred: %s" % (a["date"], a.get("outcome","?"), ctx, a.get("predicted","")))
            print("          obs : %s" % a.get("observed",""))
            if a.get("artifact"): print("          art : %s (%s)" % (a["artifact"], a.get("agent","")))
    # action summary grouped by decision
    from collections import Counter
    decisions = Counter(classify(e)[0] for e in entries)
    print("\n=== Action summary ===")
    for d in ["RETAIN", "REVISE", "REPLACE", "REMOVE"]:
        items = [e["root_cause"] for e in entries if classify(e)[0] == d]
        if items:
            print("  %s (%d):" % (d, len(items)))
            for i in items: print("    - %s" % i)
    # overall prediction accuracy
    all_atts = [a for e in entries for a in e["attempts"] if a.get("predicted")]
    hits = sum(1 for a in all_atts if a.get("outcome") != "regressed")
    print("\nPrediction accuracy: %d/%d hits (%.0f%%)" % (hits, len(all_atts), 100*hits/len(all_atts)) if all_atts else "\nNo predictions recorded yet.")

def selftest(_args):
    import tempfile, os
    global STORE
    tmp = os.path.join(tempfile.gettempdir(), "sim_selftest_%d.json" % os.getpid())
    if os.path.exists(tmp): os.remove(tmp)
    STORE = tmp
    ok = 0; fail = 0
    def check(name, cond):
        nonlocal ok, fail
        if cond: ok += 1
        else: fail += 1
        print(("PASS " if cond else "FAIL ") + name)
    # add new entry with context
    ns = argparse.Namespace(root_cause="size-guard drift", rationale="limits drifted", predicted="tree under limit", observed="427MB, FAIL->PASS", outcome="improved", artifact="memory/ops/tree_reclaim.py", agent="orchestrator", date="2026-11-27", context="cycle=77;seats_down=")
    add(ns)
    check("new entry created", len(load()["entries"]) == 1)
    # add same root-cause (case/space variant) -> merge, different context
    ns2 = argparse.Namespace(root_cause="Size Guard Drift", rationale="re-tune", predicted="hold", observed="still PASS", outcome="improved", artifact="memory/ops/tree_reclaim.py", agent="orchestrator", date="2026-11-28", context="cycle=78;seats_down=Mechanic")
    add(ns2)
    d = load(); check("same root-cause merged (1 entry, 2 attempts)", len(d["entries"])==1 and len(d["entries"][0]["attempts"])==2)
    # regression detection
    ns3 = argparse.Namespace(root_cause="heartbeat freshness", rationale="recompute", predicted="score rises", observed="still stale", outcome="regressed", artifact=None, agent="orchestrator", date="2026-11-28", context="cycle=78")
    add(ns3)
    d = load(); check("new distinct entry added (2 entries)", len(d["entries"])==2)
    hb = [e for e in d["entries"] if norm(e["root_cause"])==norm("heartbeat freshness")][0]
    dec, conf = classify(hb)
    check("single regression classified REMOVE", dec == "REMOVE")
    sz = [e for e in d["entries"] if norm(e["root_cause"])==norm("size-guard drift")][0]
    dec2, conf2 = classify(sz)
    # context shifted -> should be REVISE not RETAIN
    check("context shift downgrades retain to revise", dec2 == "REVISE")
    # test REPLACE: 2 regressed attempts
    ns4 = argparse.Namespace(root_cause="chaos SLA breach", rationale="add timeout", predicted="meet SLA", observed="still 840s", outcome="regressed", artifact=None, agent="orchestrator", date="2026-11-28", context="cycle=77")
    ns5 = argparse.Namespace(root_cause="chaos SLA breach", rationale="retry loop", predicted="meet SLA", observed="still 5700s", outcome="regressed", artifact=None, agent="orchestrator", date="2026-11-28", context="cycle=77")
    add(ns4); add(ns5)
    d = load()
    ch = [e for e in d["entries"] if norm(e["root_cause"])==norm("chaos SLA breach")][0]
    dec3, _ = classify(ch)
    check("repeated regression classified REPLACE", dec3 == "REPLACE")
    # report runs without error
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): report(None)
    check("report prints action summary", "Action summary" in buf.getvalue())
    os.remove(tmp); STORE = "memory/ops/sim_entries.json"
    print("\nselftest: %d passed, %d failed" % (ok, fail))
    sys.exit(1 if fail else 0)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("add"); a.add_argument("--root-cause", required=True); a.add_argument("--rationale"); a.add_argument("--predicted"); a.add_argument("--observed"); a.add_argument("--artifact"); a.add_argument("--agent"); a.add_argument("--outcome", choices=["improved","regressed","neutral"], default="neutral"); a.add_argument("--date"); a.add_argument("--context", help="environment context e.g. 'cycle=77;seats_down=Mechanic'")
    r = sub.add_parser("report")
    s = sub.add_parser("selftest")
    args = ap.parse_args()
    if args.cmd == "add": add(args)
    elif args.cmd == "report": report(args)
    elif args.cmd == "selftest": selftest(args)
    else: ap.print_help()

if __name__ == "__main__":
    main()
