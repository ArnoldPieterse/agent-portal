#!/usr/bin/env python3
"""
Convergence Memory Compression (Scribe Goal #5, Cycle 26)

Compresses the last N cycles of cycle narratives + closeouts into one durable
"fleet history" doc sized to fit a small-context model's token budget.
Preserves every decision that eliminated an intervention class (from
decision-autonomy-map.jsonl) verbatim. Cycles older than N are archived,
never deleted.

Usage: python memory/scribe/history_compress.py [--dry-run]
Output: memory/scribe/fleet-history.md
Archive: memory/scribe/archive/fleet-history/

Token budget: <=2000 tokens (~8000 chars). Stated here as TOKEN_BUDGET.
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# --- Configuration ---
N_CYCLES = 5          # compress last N cycles into the fleet-history doc
TOKEN_BUDGET = 2000   # max tokens for output (~4 chars/token)
CHAR_BUDGET = TOKEN_BUDGET * 4  # ~8000 chars

SCRIBE_DIR = Path("memory/scribe")
SYNTHESIS_DIR = Path("memory/synthesis")
OUTPUT_FILE = SCRIBE_DIR / "fleet-history.md"
ARCHIVE_DIR = SCRIBE_DIR / "archive" / "fleet-history"
DECISION_MAP = SCRIBE_DIR / "decision-autonomy-map.jsonl"

# Source file patterns for cycle narratives/closeouts
CYCLE_PATTERNS = [
    r"cycle-retro-(\d+)\.md",
    r"cycle-summary-(\d{4}-\d{2}-\d{2})\.md",
    r"closeout-cycle(\d+)-(\d{4}-\d{2}-\d{2})\.md",
    r"cycle-\d+-closeout-(\d{4}-\d{2}-\d{2})\.md",
]


def find_cycle_files():
    """Find all cycle narrative/closeout files, return sorted by date."""
    sources = []
    search_dirs = [SCRIBE_DIR, SYNTHESIS_DIR]
    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if not f.is_file() or f.suffix != ".md":
                continue
            name = f.name
            # Match patterns
            m = re.search(r"cycle-retro-(\d+)\.md", name)
            if m:
                cycle_num = int(m.group(1))
                sources.append((f, cycle_num, "retro"))
                continue
            m = re.search(r"closeout-cycle(\d+)-(\d{4}-\d{2}-\d{2})\.md", name)
            if m:
                cycle_num = int(m.group(1))
                date_str = m.group(2)
                sources.append((f, cycle_num, "closeout"))
                continue
            m = re.search(r"cycle-summary-(\d{4}-\d{2}-\d{2})\.md", name)
            if m:
                date_str = m.group(1)
                # Estimate cycle number from date (approximate)
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    cycle_num = (dt - datetime(2026, 11, 13)).days + 1
                except ValueError:
                    cycle_num = 0
                sources.append((f, cycle_num, "summary"))
                continue
            m = re.search(r"cycle-\d+-closeout-(\d{4}-\d{2}-\d{2})\.md", name)
            if m:
                date_str = m.group(1)
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    cycle_num = (dt - datetime(2026, 11, 13)).days + 1
                except ValueError:
                    cycle_num = 0
                sources.append((f, cycle_num, "closeout"))
                continue
    # Sort by cycle number
    sources.sort(key=lambda x: x[1])
    return sources


def compress_cycle(filepath, cycle_num, kind):
    """Compress a single cycle file into key facts (<=200 chars)."""
    text = filepath.read_text(encoding="utf-8")
    # Extract completion rate
    m = re.search(r"Completion:\*\*\s*(\d+)/\d+ goals \((\d+)%\)", text)
    if not m:
        m = re.search(r"Fleet completion:\*\*\s*(\d+)/\d+ \((\d+\.?\d*)%\)", text)
    completion = f"{m.group(1)}/{m.group(2)}%" if m else "?"

    # Extract interventions
    m = re.search(r"Interventions:\*\*\s*(\d+)", text)
    interventions = m.group(1) if m else "?"

    # Extract key decisions (lines starting with - **date** or ## Key Decisions)
    decisions = []
    in_decisions = False
    for line in text.split("\n"):
        if "Key Decision" in line or "Decision" in line and line.startswith("##"):
            in_decisions = True
            continue
        if in_decisions:
            if line.startswith("##") and "Decision" not in line:
                in_decisions = False
            elif line.strip().startswith("-") and len(line.strip()) > 10:
                decisions.append(line.strip()[:80])
    
    key_decisions = decisions[:2] if decisions else []
    
    # Build compressed entry
    label = f"C{cycle_num}"
    entry = f"- **{label}** ({kind}): {completion} complete, {interventions} intervention(s)"
    if key_decisions:
        entry += " | decisions: " + "; ".join(d[:60] for d in key_decisions)
    return entry


def load_decision_map():
    """Load all decision-autonomy-map entries (these must be preserved verbatim)."""
    if not DECISION_MAP.exists():
        return []
    entries = []
    for line in DECISION_MAP.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))
    return entries


def format_decisions_section(entries):
    """Format decision entries for the fleet-history doc."""
    lines = ["## Intervention-Class Eliminations (verbatim from decision-autonomy-map.jsonl)", ""]
    for e in entries:
        lines.append(f"### {e['decision_id']}")
        lines.append(f"- **Date:** {e['date']}")
        lines.append(f"- **Decision:** {e['decision']}")
        lines.append(f"- **Class removed:** {e['intervention_class_removed']}")
        auto_files = ", ".join(a["file"] for a in e.get("automation_built", []))
        lines.append(f"- **Automation:** {auto_files}")
        contrib = e.get("autonomy_score_contribution", {})
        lines.append(f"- **Autonomy delta:** {contrib.get('estimated_delta', '?')}")
        lines.append("")
    return "\n".join(lines)


def build_fleet_history(cycle_entries, decisions):
    """Assemble the full fleet-history document."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    doc = f"""# Fleet History (Compressed)
Generated: {now} | Source cycles: last {N_CYCLES} | Token budget: <= {TOKEN_BUDGET}

## Cycle Summaries
"""
    for entry in cycle_entries:
        doc += entry + "\n"
    
    doc += "\n" + format_decisions_section(decisions) + "\n"
    doc += f"---\n*Archived cycles (older than last {N_CYCLES}): see memory/scribe/archive/fleet-history/*\n"
    return doc


def count_tokens(text):
    """Rough token count: chars / 4."""
    return len(text) // 4


def archive_old_cycles(all_sources, keep_count):
    """Move cycle files older than the last N to archive. Never delete."""
    if len(all_sources) <= keep_count:
        return []
    old = all_sources[:len(all_sources) - keep_count]
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archived = []
    for filepath, cycle_num, kind in old:
        dest = ARCHIVE_DIR / filepath.name
        if not dest.exists():
            shutil.copy2(filepath, dest)  # copy, never move/delete
        archived.append(str(dest))
    return archived


def main():
    dry_run = "--dry-run" in sys.argv
    
    print(f"[history_compress] N={N_CYCLES}, token_budget={TOKEN_BUDGET} ({CHAR_BUDGET} chars)")
    
    # Find all cycle files
    all_sources = find_cycle_files()
    print(f"[history_compress] Found {len(all_sources)} cycle narrative files")
    for f, cn, kind in all_sources:
        print(f"  C{cn} ({kind}): {f.name}")
    
    # Take last N
    recent = all_sources[-N_CYCLES:] if len(all_sources) > N_CYCLES else all_sources
    print(f"[history_compress] Compressing last {len(recent)} cycles")
    
    # Compress each
    cycle_entries = []
    for filepath, cycle_num, kind in recent:
        entry = compress_cycle(filepath, cycle_num, kind)
        cycle_entries.append(entry)
    
    # Load decisions (must be preserved verbatim)
    decisions = load_decision_map()
    print(f"[history_compress] {len(decisions)} intervention-class eliminations to preserve")
    
    # Build document
    doc = build_fleet_history(cycle_entries, decisions)
    tokens = count_tokens(doc)
    print(f"[history_compress] Output: {len(doc)} chars ~ {tokens} tokens (budget: {TOKEN_BUDGET})")
    
    if tokens > TOKEN_BUDGET:
        # Trim cycle entries to fit budget
        print("[history_compress] Over budget - trimming cycle entries")
        while tokens > TOKEN_BUDGET and len(cycle_entries) > 1:
            cycle_entries.pop(0)
            doc = build_fleet_history(cycle_entries, decisions)
            tokens = count_tokens(doc)
        print(f"[history_compress] After trim: {len(cycle_entries)} entries, {tokens} tokens")
    
    # Verify: all decision IDs present in output
    missing = []
    for d in decisions:
        if d["decision_id"] not in doc:
            missing.append(d["decision_id"])
    if missing:
        print(f"[history_compress] ERROR: {len(missing)} decisions missing from output: {missing}")
        sys.exit(1)
    print(f"[history_compress] VERIFIED: all {len(decisions)} decision IDs present in output")
    
    if dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(doc)
        return
    
    # Write output
    OUTPUT_FILE.write_text(doc, encoding="utf-8")
    print(f"[history_compress] Wrote {OUTPUT_FILE}")
    
    # Archive old cycles
    archived = archive_old_cycles(all_sources, N_CYCLES)
    if archived:
        print(f"[history_compress] Archived {len(archived)} old cycle files to {ARCHIVE_DIR}/")
        for a in archived:
            print(f"  {a}")
    
    # Write evidence log
    log_entry = {
        "ts": datetime.utcnow().isoformat(),
        "cycles_compressed": len(recent),
        "decisions_preserved": len(decisions),
        "output_tokens": tokens,
        "token_budget": TOKEN_BUDGET,
        "within_budget": tokens <= TOKEN_BUDGET,
        "archived_count": len(archived),
        "output_file": str(OUTPUT_FILE),
    }
    log_file = SCRIBE_DIR / "history-compress-log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"[history_compress] Logged to {log_file}")
    print("[history_compress] DONE")


if __name__ == "__main__":
    main()
