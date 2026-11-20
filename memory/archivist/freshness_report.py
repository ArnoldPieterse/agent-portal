#!/usr/bin/env python3
"""archivist/freshness_report.py - Classify all memory/ files by freshness tier.

Tiers (by last-modified age):
  HOT    < 7 days
  WARM   7-30 days
  COLD   30-90 days
  STALE  > 90 days

Alerts: STALE files in active goal lanes get flagged.

Usage: python memory/archivist/freshness_report.py [--json]
Writes: memory/archivist/freshness-report-YYYY-MM-DD.md (or .json with --json)
"""
import os, sys, json, argparse
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
TODAY = date.today()

ACTIVE_LANES = {
    "goals", "archivist", "researcher", "builder", "designer",
    "mechanic", "scribe", "verifier", "orchestrator"
}

EXEMPT_EXTS = {".pyc", ".lock", ".tmp"}
EXEMPT_DIRS = {"__pycache__"}


def tier_for(age_days: int) -> str:
    if age_days < 7:
        return "HOT"
    elif age_days <= 30:
        return "WARM"
    elif age_days <= 90:
        return "COLD"
    else:
        return "STALE"


def scan(mem_root=None, today=None, root=None):
    mem_root = mem_root or MEM
    today = today or TODAY
    root = root or ROOT
    rows = []
    for dirpath, dirnames, filenames in os.walk(mem_root):
        dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIRS]
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXEMPT_EXTS:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            mtime = datetime.fromtimestamp(os.path.getmtime(full)).date()
            age_days = (today - mtime).days
            tier = tier_for(age_days)
            # lane = first segment relative to the MEMORY root (not dependent on
            # the dir being literally named 'memory')
            relmem = os.path.relpath(full, mem_root).replace(os.sep, "/")
            parts = relmem.split("/")
            lane = parts[0] if len(parts) > 1 else ""
            in_active_lane = lane in ACTIVE_LANES
            rows.append({
                "path": rel,
                "mtime": str(mtime),
                "age_days": age_days,
                "tier": tier,
                "lane": lane,
                "in_active_lane": in_active_lane,
                "alert": tier == "STALE" and in_active_lane,
            })
    return rows


def write_report(rows, path):
    total = len(rows)
    by_tier = {"HOT": 0, "WARM": 0, "COLD": 0, "STALE": 0}
    for r in rows:
        by_tier[r["tier"]] += 1
    alerts = [r for r in rows if r["alert"]]

    lines = []
    lines.append(f"# Freshness Report {TODAY.isoformat()}")
    lines.append("")
    lines.append(f"Total files scanned: {total}")
    lines.append("")
    lines.append("## Tier Summary")
    lines.append("")
    lines.append("| Tier | Count | % | Definition |")
    lines.append("|---|---|---|---|")
    for t in ("HOT", "WARM", "COLD", "STALE"):
        pct = 100.0 * by_tier[t] / total if total else 0
        defs = {"HOT": "<7 days", "WARM": "7-30 days", "COLD": "30-90 days", "STALE": ">90 days"}
        lines.append(f"| {t} | {by_tier[t]} | {pct:.1f}% | {defs[t]} |")
    lines.append("")

    if alerts:
        lines.append(f"## STALE Alerts (active lanes) - {len(alerts)} files")
        lines.append("")
        lines.append("| path | mtime | age_days | lane |")
        lines.append("|---|---|---|---|")
        for r in sorted(alerts, key=lambda x: -x["age_days"]):
            lines.append(f"| {r['path']} | {r['mtime']} | {r['age_days']} | {r['lane']} |")
        lines.append("")

    for t in ("HOT", "WARM", "COLD", "STALE"):
        tier_rows = [r for r in rows if r["tier"] == t]
        if not tier_rows:
            continue
        lines.append(f"## {t} ({len(tier_rows)} files)")
        lines.append("")
        shown = tier_rows[:50]
        for r in shown:
            flag = " **ALERT**" if r["alert"] else ""
            lines.append(f"- `{r['path']}` ({r['age_days']}d){flag}")
        if len(tier_rows) > 50:
            lines.append(f"- ... and {len(tier_rows) - 50} more")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report written: {os.path.relpath(path, ROOT)}")
    print(f"  Total: {total} | HOT: {by_tier['HOT']} | WARM: {by_tier['WARM']} | COLD: {by_tier['COLD']} | STALE: {by_tier['STALE']}")
    if alerts:
        print(f"  ALERTS: {len(alerts)} STALE files in active lanes")


def selftest():
    """Drive tier + alert logic with controlled mtimes (real data has no >90d files)."""
    import tempfile, shutil
    from datetime import timedelta
    base = tempfile.mkdtemp(prefix="fresh_selftest_")
    today = date.today()
    try:
        # active-lane file: memory/goals/old.md  (120d -> STALE + alert)
        act = os.path.join(base, "goals")
        os.makedirs(act)
        p_stale_act = os.path.join(act, "old.md")
        # inactive-lane file: memory/tmpcache/old.md (120d -> STALE, no alert)
        inact = os.path.join(base, "tmpcache")
        os.makedirs(inact)
        p_stale_inact = os.path.join(inact, "old.md")
        # boundary files in active lane
        p_hot   = os.path.join(act, "hot.md")    # 3d  -> HOT
        p_warm  = os.path.join(act, "warm.md")   # 15d -> WARM
        p_cold  = os.path.join(act, "cold.md")   # 60d -> COLD
        for path in (p_stale_act, p_stale_inact, p_hot, p_warm, p_cold):
            open(path, "w").write("x")
        def set_age(path, days):
            ts = (datetime.combine(today, datetime.min.time()) - timedelta(days=days)).timestamp()
            os.utime(path, (ts, ts))
        set_age(p_stale_act, 120)
        set_age(p_stale_inact, 120)
        set_age(p_hot, 3)
        set_age(p_warm, 15)
        set_age(p_cold, 60)
        # exempt file should be skipped
        p_pyc = os.path.join(act, "x.pyc"); open(p_pyc, "w").write("x"); set_age(p_pyc, 200)

        rows = scan(mem_root=base, today=today, root=os.path.dirname(base))
        by_path = {os.path.basename(r["path"]): r for r in rows}
        checks = [
            ("pyc exempted", "x.pyc" not in by_path),
            ("hot tier",     by_path.get("hot.md", {}).get("tier") == "HOT"),
            ("warm tier",    by_path.get("warm.md", {}).get("tier") == "WARM"),
            ("cold tier",    by_path.get("cold.md", {}).get("tier") == "COLD"),
            ("stale tier",   by_path.get("old.md", {}).get("tier") == "STALE"),
            ("alert fires in active lane", any(r["path"].endswith("goals/old.md") and r["alert"] for r in rows)),
            ("no alert in inactive lane",  not any(r["path"].endswith("tmpcache/old.md") and r["alert"] for r in rows)),
        ]
        ok = True
        print("SELFTEST freshness_report tier+alert logic:")
        for name, passed in checks:
            print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
            ok = ok and passed
        print(f"RESULT: {'PASS' if ok else 'FAIL'} ({sum(p for _,p in checks)}/{len(checks)})")
        return 0 if ok else 1
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    ap.add_argument("--selftest", action="store_true", help="Drive tier+alert logic with controlled mtimes")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    rows = scan()

    if args.json:
        out_path = os.path.join(MEM, "archivist", f"freshness-report-{TODAY.isoformat()}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"date": str(TODAY), "total": len(rows), "files": rows}, f, indent=2)
        print(f"JSON report: {os.path.relpath(out_path, ROOT)}")
    else:
        out_path = os.path.join(MEM, "archivist", f"freshness-report-{TODAY.isoformat()}.md")
        write_report(rows, out_path)


if __name__ == "__main__":
    main()
