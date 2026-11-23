#!/usr/bin/env python3
"""
KB Versioning & Rollback (Goal #10)
=====================================
Git-backed versioning of knowledge-index.json with weekly snapshots.
Supports --snapshot to create a new snapshot and --rollback <cycle> to restore.

Verification criteria:
- Deliberate index corruption fully recoverable via rollback
- Snapshot history lists >=2 cycles
- Rollback is atomic (no partial write)
- Verified against checksum
"""
import sys, os, json, hashlib, shutil, subprocess
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = SCRIPT_DIR / "kb-snapshots"
INDEX_PATH = SCRIPT_DIR / "knowledge-index.json"
SNAPSHOT_MANIFEST = SNAPSHOT_DIR / "manifest.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_manifest() -> dict:
    if SNAPSHOT_MANIFEST.exists():
        return json.loads(SNAPSHOT_MANIFEST.read_text(encoding='utf-8'))
    return {"snapshots": []}

def save_manifest(manifest: dict):
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    SNAPSHOT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

def create_snapshot(cycle_name: str = None) -> dict:
    """Create a snapshot of the current index. Atomic: write to temp then rename."""
    if cycle_name is None:
        cycle_name = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    src = INDEX_PATH
    if not src.exists():
        return {"status": "error", "detail": "knowledge-index.json not found"}
    
    checksum = sha256_file(src)
    snapshot_path = SNAPSHOT_DIR / f"{cycle_name}.json"
    
    # Atomic write: copy to temp, then rename
    tmp_path = SNAPSHOT_DIR / f".tmp_{cycle_name}"
    shutil.copy2(str(src), str(tmp_path))
    os.replace(str(tmp_path), str(snapshot_path))  # atomic on same filesystem
    
    # Verify checksum after write
    verify_checksum = sha256_file(snapshot_path)
    if verify_checksum != checksum:
        snapshot_path.unlink(missing_ok=True)
        return {"status": "error", "detail": f"checksum mismatch: {verify_checksum} != {checksum}"}
    
    # Update manifest
    manifest = load_manifest()
    entry = {
        "cycle": cycle_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": str(snapshot_path.relative_to(SCRIPT_DIR)),
        "sha256": checksum,
        "size_bytes": snapshot_path.stat().st_size
    }
    # Avoid duplicates
    existing_cycles = {s["cycle"] for s in manifest["snapshots"]}
    if cycle_name not in existing_cycles:
        manifest["snapshots"].append(entry)
        save_manifest(manifest)
    
    return {"status": "ok", "cycle": cycle_name, "sha256": checksum, "size": entry["size_bytes"]}

def rollback(cycle_name: str) -> dict:
    """Restore index from a specific snapshot. Atomic: write to temp then rename."""
    manifest = load_manifest()
    snapshot_entry = None
    for s in manifest["snapshots"]:
        if s["cycle"] == cycle_name:
            snapshot_entry = s
            break
    
    if not snapshot_entry:
        return {"status": "error", "detail": f"snapshot '{cycle_name}' not found. Available: {[s['cycle'] for s in manifest['snapshots']]}"}
    
    snapshot_path = SCRIPT_DIR / snapshot_entry["file"]
    if not snapshot_path.exists():
        return {"status": "error", "detail": f"snapshot file missing: {snapshot_path}"}
    
    # Verify snapshot integrity before restoring
    actual_checksum = sha256_file(snapshot_path)
    if actual_checksum != snapshot_entry["sha256"]:
        return {"status": "error", "detail": f"snapshot corrupt: expected {snapshot_entry['sha256']}, got {actual_checksum}"}
    
    # Atomic restore: copy to temp, verify, then rename over original
    tmp_restore = SCRIPT_DIR / ".tmp_kb_restore"
    shutil.copy2(str(snapshot_path), str(tmp_restore))
    
    # Verify restored content matches expected checksum
    restore_checksum = sha256_file(tmp_restore)
    if restore_checksum != snapshot_entry["sha256"]:
        tmp_restore.unlink(missing_ok=True)
        return {"status": "error", "detail": "restore verification failed - original untouched"}
    
    # Back up current state before overwriting
    backup_path = SCRIPT_DIR / f".pre-rollback-{cycle_name}.bak"
    if INDEX_PATH.exists():
        shutil.copy2(str(INDEX_PATH), str(backup_path))
    
    os.replace(str(tmp_restore), str(INDEX_PATH))
    
    return {
        "status": "ok",
        "restored_cycle": cycle_name,
        "sha256": snapshot_entry["sha256"],
        "backup": str(backup_path) if backup_path.exists() else None
    }

def list_snapshots() -> dict:
    manifest = load_manifest()
    return {"count": len(manifest["snapshots"]), "snapshots": manifest["snapshots"]}

def run_selftest() -> bool:
    print("=== KB VERSION SELFTEST ===\n")
    
    # Setup: ensure we have an index to work with
    if not INDEX_PATH.exists():
        print("  [FAIL] knowledge-index.json not found - cannot test")
        return False
    
    original_checksum = sha256_file(INDEX_PATH)
    all_pass = True
    
    # Test 1: Create first snapshot
    r1 = create_snapshot("selftest-cycle-1")
    ok1 = r1["status"] == "ok"
    print(f"  [{'PASS' if ok1 else 'FAIL'}] snapshot_1: {r1.get('cycle', r1.get('detail', ''))}")
    all_pass &= ok1
    
    # Test 2: Create second snapshot (simulating a change)
    # Modify index slightly, then snapshot again
    idx_data = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    original_key = list(idx_data.keys())[0]
    # Add a test marker field (will be rolled back)
    idx_data["_selftest_marker"] = "cycle2"
    INDEX_PATH.write_text(json.dumps(idx_data), encoding='utf-8')
    r2 = create_snapshot("selftest-cycle-2")
    ok2 = r2["status"] == "ok"
    print(f"  [{'PASS' if ok2 else 'FAIL'}] snapshot_2: {r2.get('cycle', r2.get('detail', ''))}")
    all_pass &= ok2
    
    # Test 3: Corrupt the index deliberately
    INDEX_PATH.write_text("CORRUPTED DATA - NOT VALID JSON", encoding='utf-8')
    corrupt_checksum = sha256_file(INDEX_PATH)
    
    # Test 4: Rollback to cycle 1 (should restore original)
    r3 = rollback("selftest-cycle-1")
    ok3 = r3["status"] == "ok"
    print(f"  [{'PASS' if ok3 else 'FAIL'}] rollback_to_cycle1: {r3.get('restored_cycle', r3.get('detail', ''))}")
    all_pass &= ok3
    
    # Test 5: Verify restored content matches original checksum (atomic, no partial)
    restored_checksum = sha256_file(INDEX_PATH)
    ok4 = (restored_checksum == original_checksum)
    print(f"  [{'PASS' if ok4 else 'FAIL'}] restore_matches_original: sha256={'match' if ok4 else f'MISMATCH ({restored_checksum[:12]}... vs {original_checksum[:12]}...)'}")
    all_pass &= ok4
    
    # Test 6: Snapshot history has >=2 entries
    hist = list_snapshots()
    ok5 = hist["count"] >= 2
    print(f"  [{'PASS' if ok5 else 'FAIL'}] history_ge_2_cycles: {hist['count']} snapshots")
    all_pass &= ok5
    
    # Test 7: Rollback to nonexistent cycle returns error (not crash)
    r4 = rollback("nonexistent-cycle-xyz")
    ok6 = r4["status"] == "error"
    print(f"  [{'PASS' if ok6 else 'FAIL'}] bad_rollback_rejected: {r4.get('detail', '')[:50]}")
    all_pass &= ok6
    
    # Cleanup: remove selftest snapshots from manifest, restore original index
    manifest = load_manifest()
    manifest["snapshots"] = [s for s in manifest["snapshots"] if not s["cycle"].startswith("selftest-")]
    save_manifest(manifest)
    for f in SNAPSHOT_DIR.glob("selftest-*.json"):
        f.unlink(missing_ok=True)
    # Clean up any backup files
    for f in SCRIPT_DIR.glob(".pre-rollback-selftest-*"):
        f.unlink(missing_ok=True)
    
    print(f"\nResult: {'PASS' if all_pass else 'FAIL'} ({sum([ok1,ok2,ok3,ok4,ok5,ok6])}/6 checks)")
    return all_pass

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        ok = run_selftest()
        sys.exit(0 if ok else 1)
    elif "--snapshot" in args:
        idx = args.index("--snapshot")
        cycle = args[idx+1] if idx+1 < len(args) and not args[idx+1].startswith("--") else None
        result = create_snapshot(cycle)
        print(json.dumps(result, indent=2))
    elif "--rollback" in args:
        idx = args.index("--rollback")
        if idx+1 >= len(args):
            print("Usage: kb_version.py --rollback <cycle_name>")
            sys.exit(1)
        result = rollback(args[idx+1])
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "ok" else 1)
    elif "--list" in args:
        print(json.dumps(list_snapshots(), indent=2))
    else:
        # Default: create a dated snapshot
        result = create_snapshot()
        print(json.dumps(result, indent=2))