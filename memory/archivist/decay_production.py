#!/usr/bin/env python3
"""archivist/decay_production.py - Weekly production run for Goal 3.

Runs decay scoring, auto-archives leaves scoring <0.2 (move to memory/archive/
with a pointer stub), and alerts on recently-referenced leaves (age<7d) scoring
<0.5. Designed for schtask: `python Z:\\memory\\archivist\\decay_production.py`

Exit codes: 0 = success, 1 = fatal error.
"""
import os, re, math, datetime, shutil, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
ARCHIVE_DIR = os.path.join(MEM, "archive")
LOG_FILE = os.path.join(MEM, "archivist", "decay-schtask.log")
TODAY = datetime.date.today()

ARCHIVE_THRESHOLD = 0.2
ALERT_THRESHOLD = 0.5
RECENT_DAYS = 7


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def score_leaves():
    """Score all memory leaves. Returns list of (rel_path, abs_path, age, refs, indexed, score)."""
    # Build index-linkage set
    indexed = set()
    for r, d, fs in os.walk(MEM):
        if "INDEX.md" in fs:
            try:
                for line in open(os.path.join(r, "INDEX.md"), encoding="utf-8", errors="replace"):
                    m = re.search(r"->\s*([A-Za-z0-9_./\\-]+\.\w+)", line)
                    if m:
                        indexed.add(m.group(1).replace("\\", "/"))
            except Exception:
                pass

    # Build reference counts + file list
    refs = {}
    allfiles = {}
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            allfiles[rel] = p
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for m in re.finditer(r"->\s*([A-Za-z0-9_./\\-]+\.\w+)|\]\(([A-Za-z0-9_./\\-]+\.\w+)\)", txt):
                t = (m.group(1) or m.group(2)).replace("\\", "/")
                refs[t] = refs.get(t, 0) + 1

    rows = []
    for rel, p in allfiles.items():
        if os.path.basename(rel) == "INDEX.md":
            continue
        # Skip non-content files
        ext = os.path.splitext(rel)[1].lower()
        if ext in (".pyc", ".json", ".jsonl", ".html"):
            continue
        try:
            mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).date()
        except Exception:
            continue
        age = (TODAY - mt).days
        recency = max(0.0, 1.0 - age / 90.0)
        density = math.log1p(refs.get(rel, 0)) / 3.0
        linkage = 1.0 if rel in indexed else 0.25
        score = round(0.5 * recency + 0.3 * min(density, 1.0) + 0.2 * linkage, 3)
        rows.append((rel, p, age, refs.get(rel, 0), rel in indexed, score))
    return rows


def auto_archive(rows):
    """Move files scoring < ARCHIVE_THRESHOLD to memory/archive/. Returns count."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archived = 0
    for rel, p, age, nrefs, indexed, score in rows:
        if score >= ARCHIVE_THRESHOLD:
            continue
        # Safety: never archive files referenced in last 7 days (age < RECENT_DAYS)
        if age < RECENT_DAYS:
            log(f"SKIP archive {rel} (score={score} but age={age}d < {RECENT_DAYS}d - recently modified)")
            continue
        dest = os.path.join(ARCHIVE_DIR, os.path.basename(rel))
        # Handle name collision
        if os.path.exists(dest):
            base, ext = os.path.splitext(os.path.basename(rel))
            dest = os.path.join(ARCHIVE_DIR, f"{base}_{TODAY.isoformat()}{ext}")
        try:
            shutil.move(p, dest)
            # Write pointer stub at original location
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(f"# ARCHIVED {TODAY.isoformat()}\n"
                         f"Moved to: memory/archive/{os.path.basename(dest)}\n"
                         f"Reason: decay score {score} < {ARCHIVE_THRESHOLD}\n")
            archived += 1
            log(f"ARCHIVED {rel} -> memory/archive/{os.path.basename(dest)} (score={score})")
        except Exception as e:
            log(f"ERROR archiving {rel}: {e}")
    return archived


def alert_recent_low(rows):
    """Alert on recently-referenced (age<7d) leaves scoring < ALERT_THRESHOLD. Returns count."""
    alerts = 0
    for rel, p, age, nrefs, indexed, score in rows:
        if age >= RECENT_DAYS:
            continue
        if score >= ALERT_THRESHOLD:
            continue
        # Only alert if it has SOME references (not completely orphaned)
        if nrefs == 0 and not indexed:
            continue
        alerts += 1
        log(f"ALERT {rel} (age={age}d, refs={nrefs}, indexed={'Y' if indexed else 'n'}, score={score})")
    return alerts


def main():
    log("=== decay_production.py run start ===")
    rows = score_leaves()
    log(f"Scored {len(rows)} content leaves")

    archived = auto_archive(rows)
    alerts = alert_recent_low(rows)

    # Write summary JSON for dashboard consumption
    summary = {
        "date": TODAY.isoformat(),
        "leaves_scored": len(rows),
        "archived": archived,
        "alerts": alerts,
        "lowest_scores": [
            {"file": r[0], "score": r[5], "age_d": r[2]}
            for r in sorted(rows, key=lambda x: x[5])[:10]
        ]
    }
    summary_path = os.path.join(MEM, "archivist", "freshness-latest.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    log(f"Done: {len(rows)} scored, {archived} archived, {alerts} alerts -> {os.path.relpath(summary_path, ROOT)}")
    log("=== decay_production.py run end ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
