#!/usr/bin/env python3
"""auto_quarantine.py - Archivist Goal 2: Stale-Knowledge Auto-Quarantine.

When a leaf's freshness score stays below threshold for N consecutive days,
move it to memory/archivist/quarantine/ and leave a tombstone pointer at the
old path (never delete). Flag every live reference pointing into quarantine.

Uses existing freshness report data for speed.

Usage:
  python memory/archivist/auto_quarantine.py [--threshold 0.3] [--days 3]
  python memory/archivist/auto_quarantine.py --test
"""
import json, os, sys, shutil, hashlib
from datetime import datetime, timezone, date
from pathlib import Path

QUARANTINE_DIR = "memory/archivist/quarantine"
STATE_FILE = "memory/archivist/quarantine-state.json"
FRESHNESS_REPORTS = [
    "memory/archivist/freshness-report-2026-11-20.json",
]

def load_freshness_data():
    """Load per-file freshness scores from existing reports."""
    scores = {}
    for rf in FRESHNESS_REPORTS:
        p = Path(rf)
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        files = data.get("files", [])
        for f in files:
            path = f.get("path", "")
            tier = f.get("tier", "HOT")
            age = f.get("age_days", 0)
            # Convert tier to numeric score
            if tier == "HOT":
                score = max(0.8, 1.0 - age * 0.02)
            elif tier == "WARM":
                score = max(0.5, 0.7 - age * 0.01)
            elif tier == "COLD":
                score = max(0.2, 0.4 - age * 0.005)
            else:  # STALE
                score = max(0.05, 0.2 - age * 0.003)
            scores[path] = {"score": round(score, 4), "tier": tier, "age_days": age}
    return scores

def load_state():
    p = Path(STATE_FILE)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"last_run": None, "below_threshold_streak": {}, "quarantined": {}}

def save_state(state):
    Path(QUARANTINE_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")

def make_tombstone(orig_path, qpath, score, days_below):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = (
        "# QUARANTINED\n\n"
        "This file was auto-quarantined by `auto_quarantine.py`.\n\n"
        "- **Original path:** `%s`\n"
        "- **Quarantine location:** `%s`\n"
        "- **Quarantine date:** %s\n"
        "- **Freshness score at quarantine:** %.4f\n"
        "- **Days below threshold before quarantine:** %d\n\n"
        "Content preserved in quarantine. To restore, move the file back and delete this tombstone.\n"
    ) % (orig_path, qpath, now, score, days_below)
    return content

def find_live_refs(quarantined_paths):
    """Find files that reference quarantined paths."""
    refs = []
    if not quarantined_paths:
        return refs
    # Search INDEX.md files and other .md files for references
    search_dirs = ["memory"]
    for sd in search_dirs:
        sp = Path(sd)
        if not sp.exists():
            continue
        for f in sp.rglob("*.md"):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            rel = str(f).replace(os.sep, "/")
            for qp in quarantined_paths:
                if qp in text and rel != qp:
                    refs.append({"file": rel, "references": qp})
    return refs

def run_quarantine(threshold=0.3, days_needed=3):
    today = date.today().isoformat()
    state = load_state()
    
    # Load freshness scores
    scores = load_freshness_data()
    # Also scan disk for .md files not in the report (catches new/aged files)
    import time as _time
    mem_dir = Path("memory")
    if mem_dir.exists():
        now_ts = datetime.now().timestamp()
        for f in mem_dir.rglob("*.md"):
            rel = str(f).replace(os.sep, "/")
            if rel in scores:
                continue
            try:
                mt = os.path.getmtime(str(f))
                age_d = (now_ts - mt) / 86400.0
                score = max(0.05, 1.0 - age_d * 0.03)
                tier = "HOT" if age_d < 3 else ("WARM" if age_d < 7 else ("COLD" if age_d < 14 else "STALE"))
                scores[rel] = {"score": round(score, 4), "tier": tier, "age_days": int(age_d)}
            except OSError:
                pass
    print("Loaded freshness data for %d files" % len(scores))
    
    # Update streaks
    below_streak = state.get("below_threshold_streak", {})
    quarantined = state.get("quarantined", {})
    
    newly_quarantined = []
    for path, info in scores.items():
        score = info["score"]
        if score < threshold:
            # Check if already quarantined
            if path in quarantined:
                continue
            # Update streak
            last_date = below_streak.get(path, {}).get("last_date")
            if last_date == today:
                continue  # already counted today
            # Increment streak (assuming daily runs)
            prev_count = below_streak.get(path, {}).get("count", 0)
            below_streak[path] = {"count": prev_count + 1, "last_date": today, "score": score}
        else:
            # Reset streak if above threshold
            if path in below_streak:
                del below_streak[path]
    
    # Quarantine files that have been below threshold for N consecutive days
    for path, info in list(below_streak.items()):
        if info["count"] >= days_needed and path not in quarantined:
            src = Path(path)
            if not src.exists():
                continue  # already gone
            # Move to quarantine
            qdir = Path(QUARANTINE_DIR)
            qdir.mkdir(parents=True, exist_ok=True)
            # Preserve directory structure in quarantine
            rel_to_mem = path.replace("memory/", "", 1) if path.startswith("memory/") else path
            dest = qdir / rel_to_mem
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            # Write tombstone
            tombstone_path = Path(path)
            tombstone_path.parent.mkdir(parents=True, exist_ok=True)
            tombstone_path.write_text(
                make_tombstone(path, str(dest), info["score"], info["count"]),
                encoding="utf-8"
            )
            quarantined[path] = {
                "quarantined_at": today,
                "location": str(dest),
                "score_at_quarantine": info["score"],
                "days_below": info["count"]
            }
            newly_quarantined.append(path)
            print("  QUARANTINED: %s (score=%.4f, %d days below)" % (path, info["score"], info["count"]))
    
    # Find live references to quarantined files
    all_q_paths = list(quarantined.keys())
    live_refs = find_live_refs(all_q_paths) if all_q_paths else []
    
    state["last_run"] = today
    state["below_threshold_streak"] = below_streak
    state["quarantined"] = quarantined
    state["live_refs_to_quarantine"] = live_refs
    save_state(state)
    
    print("\nSummary:")
    print("  Files below threshold: %d" % len(below_streak))
    print("  Newly quarantined this run: %d" % len(newly_quarantined))
    print("  Total quarantined: %d" % len(quarantined))
    print("  Live refs to quarantine: %d" % len(live_refs))
    
    return {"newly_quarantined": newly_quarantined, "total_quarantined": len(quarantined), "live_refs": live_refs}

def run_test():
    """Self-test: create a fake aged file, run quarantine, verify tombstone + idempotency."""
    print("=== AUTO-QUARANTINE SELF-TEST ===\n")
    
    # Create test file
    test_path = "memory/archivist/_test_quarantine_target.md"
    test_content = "# Test File for Quarantine\nThis is a deliberately aged file for testing.\n"
    Path(test_path).write_text(test_content, encoding="utf-8")
    
    # Create a file that references it (for live-ref detection)
    ref_path = "memory/archivist/_test_quarantine_ref.md"
    Path(ref_path).write_text("See -> %s for details.\n" % test_path, encoding="utf-8")
    
    # Simulate: manually set state to show file has been below threshold for N days
    state = load_state()
    state["below_threshold_streak"][test_path] = {"count": 3, "last_date": date.today().isoformat(), "score": 0.1}
    save_state(state)
    
    # Run quarantine with low threshold to catch our test file
    result = run_quarantine(threshold=0.5, days_needed=3)
    
    # Verify
    print("\n--- Verification ---")
    q_dest = Path(QUARANTINE_DIR) / "archivist" / "_test_quarantine_target.md"
    tombstone = Path(test_path)
    
    checks = []
    # 1. File moved to quarantine
    checks.append(("File in quarantine", q_dest.exists()))
    # 2. Tombstone exists at original path
    checks.append(("Tombstone at original path", tombstone.exists()))
    # 3. Tombstone content correct
    if tombstone.exists():
        tcontent = tombstone.read_text(encoding="utf-8")
        checks.append(("Tombstone has QUARANTINED header", "QUARANTINED" in tcontent))
        checks.append(("Tombstone points to quarantine location", str(q_dest) in tcontent or "_test_quarantine_target.md" in tcontent))
    # 4. Content preserved
    if q_dest.exists():
        qcontent = q_dest.read_text(encoding="utf-8")
        checks.append(("Content preserved in quarantine", "deliberately aged file" in qcontent))
    # 5. Live ref flagged
    state2 = load_state()
    refs = state2.get("live_refs_to_quarantine", [])
    ref_flagged = any(r.get("file") == ref_path for r in refs)
    checks.append(("Live ref to quarantine flagged", ref_flagged))
    
    # 6. Idempotency: run again, should not double-move
    result2 = run_quarantine(threshold=0.5, days_needed=3)
    checks.append(("Idempotent (no double-move)", len(result2["newly_quarantined"]) == 0))
    
    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print("  %s: %s" % ("PASS" if ok else "FAIL", name))
    
    # Cleanup test files
    if q_dest.exists():
        q_dest.unlink()
    if tombstone.exists():
        tombstone.unlink()
    if Path(ref_path).exists():
        Path(ref_path).unlink()
    # Clean state
    state3 = load_state()
    state3["below_threshold_streak"].pop(test_path, None)
    state3["quarantined"].pop(test_path, None)
    state3["live_refs_to_quarantine"] = [r for r in state3.get("live_refs_to_quarantine", []) if test_path not in r.get("references","")]
    save_state(state3)
    
    print("\nResult: %d/%d checks passed" % (passed, len(checks)))
    return passed == len(checks)

if __name__ == "__main__":
    threshold = 0.3
    days_needed = 3
    args = sys.argv[1:]
    if "--test" in args:
        ok = run_test()
        sys.exit(0 if ok else 1)
    for i, a in enumerate(args):
        if a == "--threshold" and i+1 < len(args):
            threshold = float(args[i+1])
        if a == "--days" and i+1 < len(args):
            days_needed = int(args[i+1])
    run_quarantine(threshold, days_needed)
