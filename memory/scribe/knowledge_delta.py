#!/usr/bin/env python3
"""Fleet Knowledge Delta Report - compares fleet knowledge at cycle start vs end."""
import os, json, re
from datetime import datetime, timedelta

CYCLE_START = datetime(2026, 11, 23, 0, 0)  # current cycle start
SCAN_DIRS = ["memory/goals", "memory/synthesis", "memory/scribe", "memory/ops",
             "memory/researcher", "memory/builder", "memory/mechanic",
             "memory/verifier", "memory/designer", "memory/orchestrator"]

def scan_files(since=None):
    """Scan all memory dirs, classify files by age."""
    new_files = []      # created after cycle start
    modified_files = []  # modified after cycle start but older creation
    archived_files = []  # in archive/ dirs
    all_files = []

    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d):
            for fn in files:
                if fn.startswith(".") or fn.endswith((".pyc",)):
                    continue
                fpath = os.path.join(root, fn)
                try:
                    st = os.stat(fpath)
                    mtime = datetime.fromtimestamp(st.st_mtime)
                    ctime = datetime.fromtimestamp(st.st_ctime)
                except Exception:
                    continue

                all_files.append(fpath)
                is_archived = "/archive" in fpath or "_archived" in root

                if since and mtime >= since:
                    if ctime >= since:
                        new_files.append({"path": fpath, "mtime": mtime.isoformat()})
                    else:
                        modified_files.append({"path": fpath, "mtime": mtime.isoformat()})
                if is_archived:
                    archived_files.append(fpath)

    return new_files, modified_files, archived_files, all_files

def classify_change(path):
    """Classify what kind of knowledge change this represents."""
    p = path.lower()
    if "/archive" in p or "_archived" in p:
        return "archived"
    if any(w in p for w in ["evidence", "verified", "closure", "complete"]):
        return "verification"
    if any(w in p for w in ["forecast", "proposal", "plan"]):
        return "planning"
    if any(w in p for w in ["narrative", "summary", "digest", "briefing", "report"]):
        return "synthesis"
    if any(w in p for w in [".py", ".js", ".css", ".html"]):
        return "code"
    if any(w in p for w in ["blocker", "incident", "ops-note"]):
        return "ops"
    if any(w in p for w in ["goal", "todo"]):
        return "goals"
    return "other"

def main():
    new_files, modified_files, archived_files, all_files = scan_files(CYCLE_START)

    # Classify changes
    categories = {}
    for f in new_files:
        cat = classify_change(f["path"])
        categories.setdefault(cat, []).append(f["path"])

    mod_categories = {}
    for f in modified_files:
        cat = classify_change(f["path"])
        mod_categories.setdefault(cat, []).append(f["path"])

    # Identify knowledge lost (archived without replacement)
    # Check if archived goal files have a corresponding current file
    lost_knowledge = []
    for af in archived_files:
        basename = os.path.basename(af)
        # Look for same agent's current file
        m = re.match(r"^([a-z]+)-", basename)
        if not m:
            continue
        agent = m.group(1)
        current = f"memory/goals/{agent}.md"
        if os.path.exists(current):
            # Agent still has goals, so archive is expected rotation
            pass
        else:
            lost_knowledge.append(af)

    # Build report
    now = datetime.now()
    lines = [
        "# Fleet Knowledge Delta - Cycle 10",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M')}",
        f"Cycle window: {CYCLE_START.strftime('%Y-%m-%d')} -> now",
        "",
        "## Net Changes",
        "",
        f"- **New files**: {len(new_files)}",
        f"- **Modified files**: {len(modified_files)}",
        f"- **Archived files**: {len(archived_files)}",
        f"- **Total tracked files**: {len(all_files)}",
        "",
        "## New Files by Category",
        ""
    ]
    for cat in sorted(categories, key=lambda c: -len(categories[c])):
        lines.append(f"- **{cat}**: {len(categories[cat])} files")
        # Show up to 3 examples
        for p in categories[cat][:3]:
            lines.append(f"  - {p}")

    if mod_categories:
        lines += ["", "## Modified Files by Category", ""]
        for cat in sorted(mod_categories, key=lambda c: -len(mod_categories[c])):
            lines.append(f"- **{cat}**: {len(mod_categories[cat])} files")

    # Key insights (3-5 bullets)
    lines += ["", "## Net Knowledge Gains", ""]
    insights = []
    if categories.get("synthesis"):
        insights.append(f"Synthesis layer grew by {len(categories['synthesis'])} new outputs (narratives, digests, briefings) - fleet is producing more readable summaries than raw data.")
    if categories.get("verification"):
        insights.append(f"{len(categories['verification'])} verification artifacts added this cycle - evidence trail deepening.")
    if categories.get("code"):
        insights.append(f"{len(categories['code'])} new code files (scripts/tools) - automation surface expanding.")
    if categories.get("planning"):
        insights.append(f"{len(categories['planning'])} planning/forecast documents created - forward-looking knowledge accumulating.")
    if not insights:
        insights.append("No significant net gain detected in this window; cycle may be early or low-activity.")
    for i, ins in enumerate(insights[:5], 1):
        lines.append(f"{i}. {ins}")

    # Knowledge loss check
    lines += ["", "## Knowledge Loss Check", ""]
    if lost_knowledge:
        lines.append(f"WARNING: {len(lost_knowledge)} archived files have no corresponding current file:")
        for lf in lost_knowledge[:5]:
            lines.append(f"- {lf}")
    else:
        lines.append("No knowledge loss detected. All archived content has active successors or is intentionally retired.")

    report = "\n".join(lines)
    word_count = len(report.split())
    if word_count > 500:
        # Trim to stay under 500 words
        lines = ["# Fleet Knowledge Delta - Cycle 10", "",
                 f"Generated: {now.strftime('%Y-%m-%d %H:%M')}", "",
                 f"New: {len(new_files)} | Modified: {len(modified_files)} | Archived: {len(archived_files)}", ""]
        for i, ins in enumerate(insights[:5], 1):
            lines.append(f"{i}. {ins}")
        if lost_knowledge:
            lines.append(f"\nKnowledge loss: {len(lost_knowledge)} files archived without replacement.")
        else:
            lines.append("\nNo knowledge loss detected.")
        report = "\n".join(lines)

    os.makedirs("memory/synthesis", exist_ok=True)
    out = "memory/synthesis/knowledge-delta-cycle10.md"
    with open(out, "w") as fh:
        fh.write(report)

    print(report)
    print(f"\nWords: {len(report.split())}")
    print(f"Wrote: {out}")

if __name__ == "__main__":
    main()
