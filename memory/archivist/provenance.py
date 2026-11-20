#!/usr/bin/env python3
"""provenance.py — Archivist Goal 9: Provenance Tracking for memory/ files.

Records for every memory/ file: who created it (agent), when, what triggered it.
Backfills from git log + file headers + path heuristics.

Usage:
  python memory/archivist/provenance.py --init          # backfill all files
  python memory/archivist/provenance.py --file <path>   # query one file
  python memory/archivist/provenance.py --stats         # coverage summary
"""
import json, os, re, sys, subprocess
from datetime import datetime
from pathlib import Path

PROV_FILE = "memory/archivist/provenance-data.json"
MEMORY_DIR = "memory"
AGENTS = ("orchestrator","researcher","builder","archivist","scribe",
          "verifier","designer","mechanic")

def git_log_for_file(relpath: str) -> dict | None:
    """Get first (oldest) commit info for a file from git."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H|%an|%ad", "--date=short",
             "--follow", "--", relpath],
            capture_output=True, text=True, timeout=10, cwd="."
        )
        if out.returncode == 0 and out.stdout.strip():
            lines = out.stdout.strip().splitlines()
            oldest = lines[-1]  # git log is newest-first
            parts = oldest.split("|")
            return {"commit": parts[0][:8], "author": parts[1], "date": parts[2]}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None

def infer_agent_from_path(relpath: str) -> str | None:
    """Infer creating agent from file path."""
    low = relpath.lower()
    for a in AGENTS:
        if f"/{a}/" in low or f"\\{a}\\" in low or low.startswith(f"{a}/"):
            return a
    # Check filename patterns
    for a in AGENTS:
        if a in low:
            return a
    return None

def infer_agent_from_header(text: str) -> str | None:
    """Look for agent name in first 10 lines."""
    head = "\n".join(text.splitlines()[:10]).lower()
    for a in AGENTS:
        if a in head:
            return a
    return None

def infer_trigger(text: str, relpath: str) -> str | None:
    """Infer what triggered file creation (goal ref, cycle, etc)."""
    # Look for goal references
    m = re.search(r"goal\s*(\d+)", text[:500], re.IGNORECASE)
    if m:
        return f"goal-{m.group(1)}"
    # Cycle references
    m = re.search(r"cycle[- ]?(\d+)", text[:500] + relpath, re.IGNORECASE)
    if m:
        return f"cycle-{m.group(1)}"
    # Date-stamped files often triggered by ops events
    if "evidence" in relpath.lower():
        return "verification-run"
    if "report" in relpath.lower():
        return "report-generation"
    if "sweep" in relpath.lower() or "audit" in relpath.lower():
        return "scheduled-sweep"
    return None

def scan_memory_files() -> list[str]:
    """List all files under memory/."""
    files = []
    mem = Path(MEMORY_DIR)
    if not mem.exists():
        return files
    for p in sorted(mem.rglob("*")):
        if p.is_file() and p.suffix not in {".png",".jpg",".log",".zip",".pyc"}:
            rel = p.as_posix()
            # Skip very large binary-like files
            if p.stat().st_size > 5_000_000:
                continue
            files.append(rel)
    return files

def build_provenance(relpath: str) -> dict:
    """Build provenance record for one file."""
    path = Path(relpath)
    if not path.exists():
        return {"file": relpath, "error": "not found"}
    
    mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    
    # Try git first
    git_info = git_log_for_file(relpath)
    
    # Read header for agent inference
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:2000]
    except Exception:
        text = ""
    
    agent = None
    if git_info and git_info.get("author"):
        author_low = git_info["author"].lower()
        for a in AGENTS:
            if a in author_low:
                agent = a
                break
    if not agent:
        agent = infer_agent_from_header(text)
    if not agent:
        agent = infer_agent_from_path(relpath)
    
    trigger = infer_trigger(text, relpath)
    
    rec = {
        "file": relpath,
        "agent": agent or "unknown",
        "created": git_info["date"] if git_info else mtime[:10],
        "modified": mtime,
        "trigger": trigger or "unclassified",
        "source": "git" if git_info else "heuristic"
    }
    return rec

def cmd_init():
    """Backfill provenance for all memory/ files."""
    files = scan_memory_files()
    records = []
    for i, f in enumerate(files):
        rec = build_provenance(f)
        records.append(rec)
        if (i + 1) % 200 == 0:
            print(f"  processed {i+1}/{len(files)}...", file=sys.stderr)
    
    # Stats
    total = len(records)
    with_agent = sum(1 for r in records if r.get("agent") != "unknown")
    with_trigger = sum(1 for r in records if r.get("trigger") not in (None, "unclassified"))
    coverage = round(with_agent / max(total, 1) * 100, 1)
    
    data = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generator": "Archivist / provenance.py --init",
        "total_files": total,
        "agent_coverage_pct": coverage,
        "trigger_coverage_pct": round(with_trigger / max(total, 1) * 100, 1),
        "records": records
    }
    
    os.makedirs(os.path.dirname(PROV_FILE) or ".", exist_ok=True)
    with open(PROV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Provenance init complete: {PROV_FILE} ({os.path.getsize(PROV_FILE)} B)")
    print(f"  Files scanned: {total}")
    print(f"  Agent identified: {with_agent}/{total} ({coverage}%)")
    print(f"  Trigger classified: {with_trigger}/{total} ({data['trigger_coverage_pct']}%)")
    return 0

def cmd_file(target: str):
    """Query provenance for a single file."""
    # Try loading existing data first
    if os.path.exists(PROV_FILE):
        with open(PROV_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data.get("records", []):
            if rec["file"] == target or rec["file"].endswith(target):
                print(json.dumps(rec, indent=2))
                return 0
    # Fallback: build on the fly
    rec = build_provenance(target)
    print(json.dumps(rec, indent=2))
    return 0

def cmd_stats():
    """Print coverage summary."""
    if not os.path.exists(PROV_FILE):
        print("No provenance data yet. Run --init first.")
        return 1
    with open(PROV_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Provenance stats (generated {data['generated']}):")
    print(f"  Total files: {data['total_files']}")
    print(f"  Agent coverage: {data['agent_coverage_pct']}%")
    print(f"  Trigger coverage: {data['trigger_coverage_pct']}%")
    
    # Per-agent breakdown
    from collections import Counter
    agent_counts = Counter(r.get("agent","unknown") for r in data["records"])
    print("\n  Per-agent:")
    for agent, count in agent_counts.most_common():
        print(f"    {agent:<14} {count}")
    return 0

def main():
    if "--init" in sys.argv:
        sys.exit(cmd_init())
    elif "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            sys.exit(cmd_file(sys.argv[idx+1]))
        else:
            print("Usage: --file <path>", file=sys.stderr)
            sys.exit(1)
    elif "--stats" in sys.argv:
        sys.exit(cmd_stats())
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
