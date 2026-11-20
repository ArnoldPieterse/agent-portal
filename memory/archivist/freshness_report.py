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


def scan():
    rows = []
    for dirpath, dirnames, filenames in os.walk(MEM):
        dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIRS]
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXEMPT_EXTS:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            mtime = datetime.fromtimestamp(os.path.getmtime(full)).date()
            age_days = (TODAY - mtime).days
            tier = tier_for(age_days)
            parts = rel.replace("memory/", "").split("/")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    args = ap.parse_args()

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
