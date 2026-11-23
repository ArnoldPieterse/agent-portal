#!/usr/bin/env python3
"""archivist/kb_delta.py - Knowledge Delta Feed.

Emit a compact JSON diff of what changed in the KB since last cycle:
  {added[], changed[], deleted[], affected_facts[]}

Usage:
  python memory/archivist/kb_delta.py [--selftest]

State: memory/archivist/.kb_delta_state.json (previous snapshot)
Output: memory/archivist/kb-delta-YYYY-MM-DD.json
"""
import os, sys, json, hashlib, argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MEM = ROOT / "memory"
STATE_FILE = MEM / "archivist" / ".kb_delta_state.json"
KNOWLEDGE_INDEX = MEM / "archivist" / "knowledge-index.json"
TODAY = date.today()

EXEMPT_DIRS = {"__pycache__", ".git", "search-index"}
EXEMPT_EXTS = {".pyc", ".lock", ".tmp", ".jsonl"}


def compute_snapshot():
    """Compute md5 hash for every file in memory/. Returns {rel_path: md5}."""
    snapshot = {}
    for dirpath, dirnames, filenames in os.walk(MEM):
        dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIRS]
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXEMPT_EXTS:
                continue
            full = Path(dirpath) / fn
            rel = str(full.relative_to(ROOT)).replace(os.sep, "/")
            try:
                h = hashlib.md5(full.read_bytes()).hexdigest()[:12]
            except (OSError, PermissionError):
                continue
            snapshot[rel] = h
    return snapshot


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return None


def save_state(snapshot):
    STATE_FILE.write_text(json.dumps({"date": TODAY.isoformat(), "files": snapshot}, indent=0), encoding="utf-8")


def compute_delta(prev, curr):
    """Compute add/change/delete sets between two snapshots."""
    prev_files = prev.get("files", {}) if prev else {}
    
    added = []
    changed = []
    deleted = []
    
    for path in sorted(curr.keys()):
        if path not in prev_files:
            added.append(path)
        elif prev_files[path] != curr[path]:
            changed.append(path)
    
    for path in sorted(prev_files.keys()):
        if path not in curr:
            deleted.append(path)
    
    # Cross-reference with knowledge-index.json for affected facts
    affected_facts = []
    if KNOWLEDGE_INDEX.exists():
        try:
            ki = json.loads(KNOWLEDGE_INDEX.read_text(encoding="utf-8"))
            changed_set = set(added + changed)
            if isinstance(ki, list):
                for fact in ki:
                    src = fact.get("source_file", "")
                    if src in changed_set:
                        affected_facts.append({
                            "fact_id": fact.get("id", ""),
                            "subject": fact.get("subject", ""),
                            "source": src,
                            "change_type": "added" if src in set(added) else "changed"
                        })
            elif isinstance(ki, dict) and "facts" in ki:
                for fact in ki["facts"]:
                    src = fact.get("source_file", "")
                    if src in changed_set:
                        affected_facts.append({
                            "fact_id": fact.get("id", ""),
                            "subject": fact.get("subject", ""),
                            "source": src,
                            "change_type": "added" if src in set(added) else "changed"
                        })
        except (json.JSONDecodeError, KeyError):
            pass
    
    return {
        "date": TODAY.isoformat(),
        "added": added,
        "changed": changed,
        "deleted": deleted,
        "affected_facts": affected_facts[:50],  # cap for compactness
        "summary": {
            "total_added": len(added),
            "total_changed": len(changed),
            "total_deleted": len(deleted),
            "total_affected_facts": len(affected_facts)
        }
    }


def run_selftest():
    """Self-test: create controlled edits, verify delta correctness."""
    import shutil
    print("=== KB DELTA SELFTEST ===")
    
    test_dir = MEM / "_delta_test"
    results = []
    
    # Clean up from previous runs
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    
    # Phase 1: Create initial files and take first snapshot
    f1 = test_dir / "alpha.md"
    f2 = test_dir / "beta.md"
    f1.write_text("# Alpha v1\nOriginal content.\n", encoding="utf-8")
    f2.write_text("# Beta v1\nStable content.\n", encoding="utf-8")
    
    snap1 = compute_snapshot()
    save_state(snap1)
    
    # Phase 2: Make controlled edits
    # - Modify alpha (change)
    f1.write_text("# Alpha v2\nModified content.\n", encoding="utf-8")
    # - Add gamma (add)
    f3 = test_dir / "gamma.md"
    f3.write_text("# Gamma\nNew file.\n", encoding="utf-8")
    # - Delete beta (delete)
    f2.unlink()
    
    snap2 = compute_snapshot()
    delta = compute_delta({"files": snap1}, snap2)
    
    rel_alpha = str(f1.relative_to(ROOT)).replace(os.sep, "/")
    rel_beta = str(f2.relative_to(ROOT)).replace(os.sep, "/")
    rel_gamma = str(f3.relative_to(ROOT)).replace(os.sep, "/")
    
    # Check: alpha is in changed
    check1 = rel_alpha in delta["changed"]
    results.append(("change_detected", rel_alpha, check1, f"changed={delta['summary']['total_changed']}"))
    
    # Check: gamma is in added
    check2 = rel_gamma in delta["added"]
    results.append(("add_detected", rel_gamma, check2, f"added={delta['summary']['total_added']}"))
    
    # Check: beta is in deleted
    check3 = rel_beta in delta["deleted"]
    results.append(("delete_detected", rel_beta, check3, f"deleted={delta['summary']['total_deleted']}"))
    
    # Check: valid JSON (serialize and re-parse)
    try:
        s = json.dumps(delta)
        parsed = json.loads(s)
        check4 = True
    except Exception as e:
        check4 = False
    results.append(("valid_json", "delta", check4, f"size={len(json.dumps(delta))} bytes"))
    
    # Check: quiet cycle delta is < 2KB
    # Re-snapshot (no changes) and compute delta against itself
    snap3 = compute_snapshot()
    quiet_delta = compute_delta({"files": snap3}, snap3)
    quiet_size = len(json.dumps(quiet_delta))
    check5 = quiet_size < 2048
    results.append(("quiet_under_2kb", f"{quiet_size}B", check5, f"quiet delta size"))
    
    # Check: two consecutive runs with no change produce empty sets
    check6 = len(quiet_delta["added"]) == 0 and len(quiet_delta["changed"]) == 0 and len(quiet_delta["deleted"]) == 0
    results.append(("idempotent_quiet", "no-change run", check6, "empty add/change/delete"))
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)
    # Restore state to current snapshot
    save_state(compute_snapshot())
    
    # Report
    print(f"\n{'Test':<20} {'Detail':<50} {'Pass'}")
    print("-" * 75)
    all_pass = True
    for name, detail, passed, note in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"{name:<20} {detail[:48]:<50} {status}")
    
    print(f"\n{'='*75}")
    print(f"SELFTEST {'PASS' if all_pass else 'FAIL'} ({sum(1 for r in results if r[2])}/{len(results)} checks)")
    
    # Write the test delta as artifact
    out = MEM / "archivist" / f"kb-delta-selftest-{TODAY.isoformat()}.json"
    out.write_text(json.dumps(delta, indent=2), encoding="utf-8")
    print(f"Artifact: {out.relative_to(ROOT)}")
    
    return 0 if all_pass else 1


def main():
    ap = argparse.ArgumentParser(description="Knowledge Delta Feed")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    
    if args.selftest:
        sys.exit(run_selftest())
    
    # Normal run
    curr = compute_snapshot()
    prev = load_state()
    delta = compute_delta(prev, curr)
    
    out_path = MEM / "archivist" / f"kb-delta-{TODAY.isoformat()}.json"
    out_path.write_text(json.dumps(delta, indent=2), encoding="utf-8")
    
    # Save current snapshot as new state
    save_state(curr)
    
    s = delta["summary"]
    print(f"KB Delta {TODAY.isoformat()}: +{s['total_added']} ~{s['total_changed']} -{s['total_deleted']} (facts: {s['total_affected_facts']})")
    print(f"Output: {out_path.relative_to(ROOT)} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
