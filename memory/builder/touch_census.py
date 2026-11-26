#!/usr/bin/env python3
"""
Builder Goal #6 — Human-Touchpoint Census + Removal Tracker.
Census of every human touch (unblock / redirect / ratify / approval) across the last N
cycles, parsed from the intervention log, each classified deterministically as
removable-now / removable-later / required, with removal progress tracked over time.

Inputs (defaults):
  interventions : memory/ops/human-interventions.jsonl   records {ts,cycle,agent,type,context}
  removed       : memory/ops/touches-removed.json        list of already-removed touch keys
Outputs:
  touches.jsonl             latest census snapshot: one line per touch + a trailing summary
  touch-census-history.jsonl  append-only summary-per-run (so the count drop is observable)

Classification (deterministic, same input -> same output):
  required        : context matches a hard-human keyword (account/credential/password/manual/
                    human-only/legal/compliance/payment/arnold) — cannot be automated away.
  removable-now   : type in {unblock, redirect} with no required keyword — the first class to
                    eliminate for autonomy convergence.
  removable-later : ratify/approval or other types (no required keyword) — minimizable later.

Usage:
  python memory/builder/touch_census.py                 # census live log -> touches.jsonl
  python memory/builder/touch_census.py --recent 5      # only the last 5 distinct cycles
  python memory/builder/touch_census.py --selftest
"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "memory" / "ops"
INTERVENTIONS = OPS / "human-interventions.jsonl"
REMOVED_FILE = OPS / "touches-removed.json"
OUT_JSONL = OPS / "touches.jsonl"
HISTORY = OPS / "touch-census-history.jsonl"

REQUIRED_KEYWORDS = ("account", "credential", "password", "manual",
                     "human-only", "legal", "compliance", "payment", "arnold")
NOW_TYPES = {"unblock", "redirect"}
LATER_TYPES = {"ratify", "ratification", "approve", "approval"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_type(t):
    t = (t or "").strip().lower()
    if t in NOW_TYPES:
        return t
    if t in LATER_TYPES:
        return "ratify"
    return t or "other"


def classify(type_norm, context):
    ctx = (context or "").lower()
    if any(k in ctx for k in REQUIRED_KEYWORDS):
        return "required"
    if type_norm in NOW_TYPES:
        return "removable-now"
    return "removable-later"


def touch_key(rec):
    return f"{rec.get('cycle')}:{rec.get('agent')}:{normalize_type(rec.get('type'))}:{rec.get('ts')}"


def load_interventions(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        out.append(d)
    return out


def census(interventions=None, removed=None, recent=None):
    if interventions is None:
        interventions = load_interventions(INTERVENTIONS)
    if removed is None:
        removed = set(json.loads(REMOVED_FILE.read_text(encoding="utf-8"))) if REMOVED_FILE.exists() else set()
    # restrict to last N distinct cycles (largest cycle values) when requested.
    if recent:
        cycles = sorted({r.get("cycle") for r in interventions if isinstance(r.get("cycle"), int)}, reverse=True)
        keep = set(cycles[:recent])
        interventions = [r for r in interventions if r.get("cycle") in keep]
    records = []
    for r in sorted(interventions, key=lambda x: (x.get("cycle", 0), x.get("ts", ""), x.get("agent", ""))):
        tn = normalize_type(r.get("type"))
        cls = classify(tn, r.get("context"))
        k = touch_key(r)
        records.append({"key": k, "cycle": r.get("cycle"), "ts": r.get("ts"),
                        "agent": r.get("agent"), "type": tn,
                        "classification": cls, "removed": k in removed})
    total = len(records)
    active = [x for x in records if not x["removed"]]
    by_cls = {c: sum(1 for x in active if x["classification"] == c)
              for c in ("removable-now", "removable-later", "required")}
    by_cycle = {}
    for x in active:
        by_cycle[x["cycle"]] = by_cycle.get(x["cycle"], 0) + 1
    removal_rate = round(1 - (len(active) / total), 4) if total else 0.0
    summary = {"type": "census", "ts": _now(), "total": total, "active": len(active),
               "removed": total - len(active), "by_classification": by_cls,
               "by_cycle": by_cycle, "removal_rate": removal_rate}
    return records, summary


def emit(records, summary):
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.write(json.dumps(summary) + "\n")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: summary[k] for k in
                            ("type", "ts", "total", "active", "removed", "by_classification", "removal_rate")}) + "\n")


def _selftest():
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp(prefix="touch_selftest_"))
    failures = []
    try:
        seed = [
            {"ts": "2026-11-18T14:00:00+00:00", "cycle": 5, "agent": "Researcher", "type": "approve", "context": "goal ratification"},
            {"ts": "2026-11-17T09:15:00+00:00", "cycle": 3, "agent": "Builder", "type": "unblock", "context": "clear lane blocker"},
            {"ts": "2026-11-16T17:30:00+00:00", "cycle": 2, "agent": "Orchestrator", "type": "redirect", "context": "reassign seat"},
            {"ts": "2026-11-20T10:30:00+00:00", "cycle": 8, "agent": "Mechanic", "type": "unblock", "context": "connect account to provider"},
        ]
        iv = tmp / "iv.jsonl"
        iv.write_text("\n".join(json.dumps(x) for x in seed), encoding="utf-8")
        # (1) census reproduces the known seeded set with correct classification.
        recs, summ = census(interventions=load_interventions(iv), removed=set())
        if len(recs) != 4:
            failures.append(f"expected 4 touches, got {len(recs)}")
        expect = {
            "5:Researcher:ratify:2026-11-18T14:00:00+00:00": "removable-later",
            "3:Builder:unblock:2026-11-17T09:15:00+00:00": "removable-now",
            "2:Orchestrator:redirect:2026-11-16T17:30:00+00:00": "removable-now",
            "8:Mechanic:unblock:2026-11-20T10:30:00+00:00": "required",  # 'account' keyword
        }
        for x in recs:
            if expect.get(x["key"]) != x["classification"]:
                failures.append(f"misclassified {x['key']} -> {x['classification']} (want {expect.get(x['key'])})")
        # (2) deterministic: same input twice -> identical output.
        recs2, _ = census(interventions=load_interventions(iv), removed=set())
        if [x["key"] for x in recs] != [x["key"] for x in recs2] or \
           [x["classification"] for x in recs] != [x["classification"] for x in recs2]:
            failures.append("classification not deterministic across runs")
        # (3) removal drops the active count on the next run.
        victim = "3:Builder:unblock:2026-11-17T09:15:00+00:00"
        recs3, summ3 = census(interventions=load_interventions(iv), removed={victim})
        if summ["active"] != 4 or summ3["active"] != 3:
            failures.append(f"removal did not drop count: before={summ['active']} after={summ3['active']}")
        if not any(x["key"] == victim and x["removed"] for x in recs3):
            failures.append("removed touch not marked removed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("SELFTEST FAIL")
        for f_ in failures:
            print("  -", f_)
        return 1
    print("SELFTEST PASS: seeded set reproduced with correct classification; deterministic across runs; "
          "removal drops active count (4 -> 3) and marks the touch removed.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Builder human-touchpoint census + removal tracker")
    ap.add_argument("--recent", type=int, default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-emit", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    records, summary = census(recent=args.recent)
    for r in records:
        print(json.dumps(r))
    print(json.dumps(summary))
    if not args.no_emit:
        emit(records, summary)
        print(f"[touch_census] wrote {len(records)} touches + summary -> {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
