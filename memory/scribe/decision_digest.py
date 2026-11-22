#!/usr/bin/env python3
"""Fleet Decision Digest - compresses decisions into a themed narrative.

Reads decision sources, groups by theme, highlights patterns, flags rollbacks.
Writes to memory/synthesis/decision-digest-YYYY-MM-DD.md.
Tracks last digest date in memory/synthesis/.digest_cursor.json.
"""
import json, os, re
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

# --- Config ---
SOURCES = [
    "decision-log.jsonl",                    # remediation policy rules
    "memory/synthesis/decisions.jsonl",      # cycle decisions (date + text)
]
DECISIONS_DIR = "memory/synthesis/decisions"  # individual decision leaves
CURSOR_FILE = "memory/synthesis/.digest_cursor.json"
OUTPUT_DIR = "memory/synthesis"

# --- Load cursor ---
def load_cursor():
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE) as f:
            return json.load(f)
    return {"last_digest_date": None, "last_run": None}

def save_cursor(cursor):
    with open(CURSOR_FILE, "w") as f:
        json.dump(cursor, f, indent=2)

# --- Load decisions from all sources ---
def load_decisions(since_date=None):
    """Return list of decision dicts: {date, text, source, theme}"""
    decisions = []
    
    # Source 1: decision-log.jsonl (remediation policies)
    for path in SOURCES:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Filter by date if present and since_date set
                d = rec.get("date")
                if since_date and d and d < since_date:
                    continue
                
                if "rule_id" in rec:
                    # Remediation policy rule
                    decisions.append({
                        "date": d or "policy",
                        "text": f"[{rec['rule_id']}] {rec.get('degradation_type','?')}: {rec['action']['description']}",
                        "source": "remediation_policy",
                        "theme": "operational-resilience"
                    })
                elif "decision" in rec:
                    decisions.append({
                        "date": d or "unknown",
                        "text": rec["decision"],
                        "source": "cycle-decisions",
                        "theme": classify_theme(rec["decision"])
                    })
    
    # Source 2: individual decision leaves in decisions/ dir
    if os.path.isdir(DECISIONS_DIR):
        for fname in sorted(os.listdir(DECISIONS_DIR)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(DECISIONS_DIR, fname)
            # Extract date from filename: YYYY-MM-DD-NN-...
            m = re.match(r"(\d{4}-\d{2}-\d{2})-(\d+)-(.+)\.md", fname)
            if m:
                d, num, title = m.groups()
                if since_date and d < since_date:
                    continue
                # Read first meaningful line as summary
                with open(fpath, encoding="utf-8") as f:
                    content = f.read().strip()
                    first_line = content.split("\n")[0][:200] if content else title
                decisions.append({
                    "date": d,
                    "text": first_line or title,
                    "source": "decision-leaf",
                    "theme": classify_theme(title + " " + first_line)
                })
    
    return decisions

def classify_theme(text):
    """Classify a decision into a theme bucket."""
    t = text.lower()
    if any(k in t for k in ["pointer", "index", "registry", "module"]):
        return "memory-hygiene"
    if any(k in t for k in ["portal", "ui", "css", "frontend", "click"]):
        return "portal-ui"
    if any(k in t for k in ["model", "vram", "host", "load", "oom"]):
        return "infrastructure"
    if any(k in t for k in ["goal", "cycle", "completion", "ledger"]):
        return "goal-management"
    if any(k in t for k in ["rollback", "revert", "undo", "supersede"]):
        return "corrections"
    if any(k in t for k in ["agent", "route", "handoff", "assign"]):
        return "agent-ops"
    if any(k in t for k in ["dcabots", "bot", "dca"]):
        return "projects"
    return "general"

# --- Detect rollbacks ---
def detect_rollbacks(decisions):
    """Find decisions that mention rollback/revert/supersede."""
    rollbacks = []
    for d in decisions:
        t = d["text"].lower()
        if any(k in t for k in ["rollback", "reverted", "superseded", "undone", "rejected"]):
            rollbacks.append(d)
    return rollbacks

# --- Generate narrative ---
def generate_digest(decisions, rollbacks, since_date):
    today = date.today().isoformat()
    lines = []
    lines.append(f"# Fleet Decision Digest - {today}")
    lines.append("")
    
    period = f"since {since_date}" if since_date else "all-time (first digest)"
    lines.append(f"**Period:** {period}  ")
    lines.append(f"**Total decisions:** {len(decisions)}  ")
    lines.append(f"**Rollbacks/corrections:** {len(rollbacks)}")
    lines.append("")
    
    # Group by theme
    by_theme = defaultdict(list)
    for d in decisions:
        by_theme[d["theme"]].append(d)
    
    # Sort themes by count desc
    sorted_themes = sorted(by_theme.items(), key=lambda x: -len(x[1]))
    
    lines.append("## Thematic Summary")
    lines.append("")
    for theme, items in sorted_themes:
        lines.append(f"### {theme.replace('-', ' ').title()} ({len(items)} decisions)")
        lines.append("")
        # Show up to 5 per theme, summarize rest
        shown = 0
        for item in items[:5]:
            date_str = f"[{item['date']}]" if item["date"] != "policy" else "[policy]"
            lines.append(f"- {date_str} {item['text'][:150]}")
            shown += 1
        if len(items) > 5:
            lines.append(f"- ...and {len(items)-5} more in this theme")
        lines.append("")
    
    # Rollback section
    if rollbacks:
        lines.append("## Corrections & Rollbacks")
        lines.append("")
        for r in rollbacks:
            date_str = f"[{r['date']}]" if r["date"] != "policy" else ""
            lines.append(f"- {date_str} **ROLLED BACK:** {r['text'][:150]}")
        lines.append("")
    
    # Patterns
    lines.append("## Notable Patterns")
    lines.append("")
    patterns = []
    if len(by_theme.get("memory-hygiene", [])) >= 3:
        patterns.append(f"Memory hygiene dominated with {len(by_theme['memory-hygiene'])} decisions - the fleet is stabilizing its knowledge architecture.")
    if rollbacks:
        patterns.append(f"{len(rollbacks)} corrections detected, indicating active self-correction in the decision process.")
    if len(by_theme.get("portal-ui", [])) >= 2:
        patterns.append(f"Portal/UI work accounts for {len(by_theme['portal-ui'])} decisions - frontend is an active investment area.")
    if not patterns:
        patterns.append("No dominant pattern this period; decisions are distributed across themes.")
    for p in patterns:
        lines.append(f"- {p}")
    lines.append("")
    
    # Word count check (target 500-1500)
    text = "\n".join(lines)
    wc = len(text.split())
    if wc < 500:
        # Expand with more detail per theme
        extra = []
        for theme, items in sorted_themes:
            for item in items:
                date_str = f"[{item['date']}]" if item["date"] != "policy" else "[policy]"
                extra.append(f"  - {date_str} ({item['source']}): {item['text'][:200]}")
        lines.insert(-1, "## Full Decision List")
        lines.extend(extra)
    
    return "\n".join(lines)

# --- Main ---
def main():
    cursor = load_cursor()
    since_date = cursor.get("last_digest_date")
    
    decisions = load_decisions(since_date)
    rollbacks = detect_rollbacks(decisions)
    
    if not decisions:
        print("No new decisions found since last digest. Nothing to write.")
        return
    
    digest = generate_digest(decisions, rollbacks, since_date)
    
    today = date.today().isoformat()
    out_path = os.path.join(OUTPUT_DIR, f"decision-digest-{today}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(digest)
    
    # Update cursor to latest decision date
    all_dates = [d["date"] for d in decisions if d["date"] != "policy" and d["date"] != "unknown"]
    max_date = max(all_dates) if all_dates else today
    
    cursor["last_digest_date"] = max_date
    cursor["last_run"] = datetime.now().isoformat()
    save_cursor(cursor)
    
    wc = len(digest.split())
    print(f"Digest written: {out_path}")
    print(f"  Decisions: {len(decisions)}, Rollbacks: {len(rollbacks)}, Words: {wc}")
    print(f"  Cursor advanced to: {max_date}")

if __name__ == "__main__":
    main()
