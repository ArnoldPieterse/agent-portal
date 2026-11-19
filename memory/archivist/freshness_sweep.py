#!/usr/bin/env python3
"""archivist/freshness_sweep.py - flags expired KB entries per freshness-policy.md.
Usage: python memory/archivist/freshness_sweep.py [--days N]
Writes report to memory/archivist/freshness-sweep-YYYY-MM-DD.md. Exit 0 always."""
import os, re, sys, argparse
from datetime import datetime, date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
TODAY = date.today()

# TTL in days per entry type (from freshness-policy.md)
TTL = {"fact": 90, "opinion": 30, "procedure": 180, "spec": 90, "report": 30}

EXEMPT_DIRS = {"archive", "__pycache__"}
EXEMPT_FILES = {"INDEX.md", "MEMORY.md", "TODO.md", "VLOG.txt"}


def classify(filename: str, first_line: str) -> str:
    """Classify entry type by heuristics."""
    ln = filename.lower()
    if any(k in ln for k in ("runbook", "recovery", "procedure", "howto", "recovery-matrix")):
        return "procedure"
    if any(k in ln for k in ("audit", "report", "benchmark", "scan", "digest", "sweep")):
        return "report"
    if any(k in ln for k in ("spec", "protocol", "interface", "api-ref")):
        return "spec"
    # Check first line for spec indicators
    fl = first_line.lower()
    if any(k in fl for k in ("specification", "protocol", "interface definition")):
        return "spec"
    # Default: opinion (most conservative)
    return "opinion"


def get_date_from_filename(filename: str) -> date | None:
    """Extract date from filename patterns like YYYY-MM-DD or YYYYMMDD."""
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if m:
        try: return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: pass
    m = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if m:
        try: return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: pass
    return None


def get_date_from_content(path: str) -> date | None:
    """Try to extract a date from the first few lines of content."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(500)
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})', head)
        if m:
            try: return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError: pass
    except Exception:
        pass
    return None


def sweep(max_age_days: int | None = None) -> list[dict]:
    """Scan all memory leaves and classify freshness."""
    rows = []
    for dirpath, dirnames, filenames in os.walk(MEM):
        # Prune exempt dirs
        dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIRS]
        for fn in sorted(filenames):
            if fn in EXEMPT_FILES:
                continue
            if not fn.endswith(".md"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            # Get modification date and content date
            mtime = datetime.fromtimestamp(os.path.getmtime(full)).date()
            file_date = get_date_from_filename(fn) or get_date_from_content(full) or mtime
            age_days = (TODAY - file_date).days
            # Classify
            try:
                with open(full, encoding="utf-8", errors="replace") as f:
                    first_line = f.readline().strip()
            except Exception:
                first_line = ""
            etype = classify(fn, first_line)
            ttl = TTL[etype]
            # Determine status
            if max_age_days and age_days > max_age_days:
                continue
            if age_days > 2 * ttl:
                status = "ARCHIVE_RECOMMENDED"
            elif age_days > ttl:
                status = "EXPIRED"
            else:
                status = "ok"
            rows.append({
                "path": rel, "type": etype, "ttl": ttl,
                "dated": str(file_date), "age_d": age_days, "state": status
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None, help="Only show entries older than N days")
    args = ap.parse_args()
    rows = sweep(args.days)
    expired = [r for r in rows if r["state"] != "ok"]
    ok = [r for r in rows if r["state"] == "ok"]
    report_path = os.path.join(MEM, "archivist", f"freshness-sweep-{TODAY.isoformat()}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Freshness Sweep {TODAY.isoformat()}\n\n")
        f.write(f"Total leaves: {len(rows)} | OK: {len(ok)} | Expired: {len(expired)}\n\n")
        if expired:
            f.write("## Expired / Archive-Recommended\n\n")
            f.write("| path | type | ttl_d | dated | age_d | state |\n|---|---|---|---|---|---|\n")
            for r in sorted(expired, key=lambda x: -x["age_d"]):
                f.write(f"| {r['path']} | {r['type']} | {r['ttl']} | {r['dated']} | {r['age_d']} | {r['state']} |\n")
        else:
            f.write("No expired entries. All within TTL.\n")
    print(f"Sweep complete: {len(rows)} leaves, {len(expired)} expired. Report: {os.path.relpath(report_path, ROOT)}")

if __name__ == "__main__":
    main()
