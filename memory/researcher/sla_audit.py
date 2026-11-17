#!/usr/bin/env python3
"""sla_audit.py - one-command 48h SLA audit for goal #8 (open-questions cycle-3).

Source of truth = memory/researcher/sla_registry.json (explicit sla_started per entry).
Replaces hand-computed ages in open-questions-log.md (which regressed by ~24h in pass-8).

Usage:
  python memory/researcher/sla_audit.py            # audit vs host local now
  python memory/researcher/sla_audit.py --ref 2026-11-20T09:00   # audit vs a fixed reference (mid-cycle re-audit)
  python memory/researcher/sla_audit.py --json     # machine-readable output

Exit code: 0 = zero breaches among non-resolved entries; 1 = >=1 breach; 2 = registry unreadable.
"""
import json, sys, datetime as dt
from pathlib import Path

REG = Path(__file__).with_name("sla_registry.json")


def parse_ts(s):
    return dt.datetime.strptime(s.strip(), "%Y-%m-%dT%H:%M")


def classify(entry, now, sla_h, pro_h):
    if entry.get("status") == "RESOLVED":
        res_at = parse_ts(entry["resolved_at"]) if entry.get("resolved_at") else now
        age_h = (res_at - parse_ts(entry["sla_started"])).total_seconds() / 3600.0
        return "RESOLVED", age_h
    age_h = (now - parse_ts(entry["sla_started"])).total_seconds() / 3600.0
    if age_h > sla_h:
        return "BREACH", age_h
    if age_h > pro_h:
        return "PROACTIVE", age_h
    return "OK", age_h


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    ref = None
    for i, a in enumerate(args):
        if a == "--ref":
            try:
                ref = parse_ts(args[i + 1])
            except (ValueError, IndexError) as e:
                print(f"FATAL: bad --ref value {args[i+1] if i+1 < len(args) else '(missing)'} - expected YYYY-MM-DDTHH:MM", file=sys.stderr)
                return 2
    now = ref or dt.datetime.now()

    try:
        reg = json.loads(REG.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FATAL: cannot read {REG}: {e}", file=sys.stderr)
        return 2

    sla_h, pro_h = reg["sla_hours"], reg["proactive_hours"]
    rows = []
    for e in reg["entries"]:
        cls, age_h = classify(e, now, sla_h, pro_h)
        status = e.get("status", "?")
        breach_by = (parse_ts(e["sla_started"]) + dt.timedelta(hours=sla_h)).strftime("%m-%d %H:%M") if status != "RESOLVED" else "-"
        rows.append((e["id"], cls, age_h, status, breach_by))

    breaches = [r for r in rows if r[1] == "BREACH"]
    proactives = [r for r in rows if r[1] == "PROACTIVE"]
    ok = [r for r in rows if r[1] == "OK"]
    resolved = [r for r in rows if r[1] == "RESOLVED"]

    if as_json:
        out = {
            "reference_time": now.strftime("%Y-%m-%dT%H:%M"),
            "sla_hours": sla_h, "proactive_hours": pro_h,
            "zero_breaches": len(breaches) == 0,
            "counts": {"breach": len(breaches), "proactive": len(proactives),
                       "ok": len(ok), "resolved": len(resolved)},
            "entries": [{"id": r[0], "class": r[1], "age_hours": round(r[2], 1),
                         "status": r[3], "breach_by": r[4]} for r in rows],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"SLA audit @ {now.strftime('%Y-%m-%d %H:%M')}  (SLA={sla_h}h, proactive>={pro_h}h)  registry: cycle {reg.get('cycle','?')}")
        print(f"{'entry':24s} {'class':10s} {'age':>8s}  {'breach-by':12s} status")
        print("-" * 70)
        for r in rows:
            mult = f" x{r[2]/sla_h:.2f}" if r[1] == "BREACH" else ""
            print(f"{r[0]:24s} {r[1]:10s} {r[2]:6.1f}h{mult:8s}  {r[4]:12s} {r[3]}")
        print("-" * 62)
        print(f"SUMMARY: {len(resolved)} resolved | {len(breaches)} BREACH | {len(proactives)} proactive | {len(ok)} ok")
        if breaches:
            print("BREACHES (acceptance FAIL - zero-breaches target not met):")
            for r in breaches:
                e = next(x for x in reg["entries"] if x["id"] == r[0])
                print(f"  - {r[0]}: {r[2]:.1f}h (x{r[2]/sla_h:.2f}) | owner={e.get('owner','?')} | unblock: {e.get('unblock_cmd','n/a')}")
        else:
            print("ZERO BREACHES - acceptance target MET (at this reference time).")

    return 0 if len(breaches) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
