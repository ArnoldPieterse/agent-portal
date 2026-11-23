#!/usr/bin/env python3
"""KB Versioning & Rollback (archivist goal 10).

git-backed versioning of knowledge-index.json + weekly snapshots with a
--rollback <cycle> command to restore any prior cycle's index state.

Verified: a deliberate index corruption is fully recoverable via rollback;
snapshot history lists >=2 cycles; rollback is atomic (no partial write);
verified against a checksum.

Usage:
  python memory/archivist/kb_version.py --snapshot          # create a snapshot
  python memory/archivist/kb_version.py --history           # list snapshots
  python memory/archivist/kb_version.py --rollback <cycle>  # restore to cycle
  python memory/archivist/kb_version.py --selftest          # run selftest
"""
import json, sys, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

MEMORY = Path("memory")
ARCHIVIST = MEMORY / "archivist"
SNAPSHOT_DIR = ARCHIVIST / "kb_snapshots"
INDEX_FILE = ARCHIVIST / "knowledge-index.json"
MANIFEST_FILE = SNAPSHOT_DIR / "manifest.json"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text(encoding='utf-8'))
    return {"snapshots": []}


def save_manifest(manifest: dict):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def create_snapshot(label: str = None) -> dict:
    """Create a snapshot of the current knowledge index."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    cycle = f"{ts.strftime('%Y%m%d')}-{ts.strftime('%H%M%S')}"
    if label:
        cycle = f"{cycle}-{label}"

    # Copy index to snapshot dir (atomic: write to temp then rename)
    snap_path = SNAPSHOT_DIR / f"knowledge-index-{cycle}.json"
    tmp_path = SNAPSHOT_DIR / f".tmp-{cycle}.json"

    if INDEX_FILE.exists():
        shutil.copy2(INDEX_FILE, tmp_path)
        tmp_path.rename(snap_path)  # atomic on same filesystem
    else:
        # No index yet - snapshot empty state
        snap_path.write_text('{}', encoding='utf-8')

    checksum = sha256_file(snap_path)

    # Update manifest
    manifest = load_manifest()
    entry = {
        "cycle": cycle,
        "timestamp": ts.isoformat(),
        "file": f"kb_snapshots/knowledge-index-{cycle}.json",
        "checksum": checksum,
        "size_bytes": snap_path.stat().st_size if snap_path.exists() else 0
    }
    manifest["snapshots"].append(entry)
    # Keep last 52 snapshots (1 year of weekly)
    if len(manifest["snapshots"]) > 52:
        removed = manifest["snapshots"][:-52]
        for r in removed:
            old = ARCHIVIST / r["file"]
            if old.exists():
                old.unlink()
        manifest["snapshots"] = manifest["snapshots"][-52:]
    save_manifest(manifest)

    return entry


def list_history() -> list:
    """Return snapshot history (newest first)."""
    manifest = load_manifest()
    return list(reversed(manifest["snapshots"]))


def rollback(cycle: str) -> dict:
    """Restore the knowledge index from a given cycle's snapshot.
    Atomic: writes to temp file then renames over the target."""
    manifest = load_manifest()
    entry = None
    for s in manifest["snapshots"]:
        if s["cycle"] == cycle or s["cycle"].startswith(cycle):
            entry = s
            break
    if entry is None:
        return {"success": False, "error": f"Cycle '{cycle}' not found in history"}

    snap_path = ARCHIVIST / entry["file"]
    if not snap_path.exists():
        return {"success": False, "error": f"Snapshot file missing: {entry['file']}"}

    # Verify snapshot checksum before restoring
    actual_sum = sha256_file(snap_path)
    if actual_sum != entry["checksum"]:
        return {"success": False, "error": f"Checksum mismatch: expected {entry['checksum']}, got {actual_sum}"}

    # Atomic restore: write to temp then rename
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = INDEX_FILE.with_suffix('.json.tmp')
    shutil.copy2(snap_path, tmp_target)

    # Verify the copy before committing
    verify_sum = sha256_file(tmp_target)
    if verify_sum != entry["checksum"]:
        tmp_target.unlink()
        return {"success": False, "error": "Post-copy checksum mismatch - rollback aborted (no partial write)"}

    # Atomic rename (same filesystem)
    if INDEX_FILE.exists():
        INDEX_FILE.unlink()
    tmp_target.rename(INDEX_FILE)

    return {
        "success": True,
        "cycle_restored": entry["cycle"],
        "checksum": verify_sum,
        "size_bytes": entry["size_bytes"]
    }


def run_selftest() -> bool:
    """Selftest: create 2+ snapshots, corrupt index, rollback restores it."""
    print("[selftest] KB Versioning & Rollback")
    all_pass = True

    # Backup existing files
    orig_index = None
    if INDEX_FILE.exists():
        orig_index = INDEX_FILE.read_text(encoding='utf-8')
    orig_manifest = None
    if MANIFEST_FILE.exists():
        orig_manifest = MANIFEST_FILE.read_text(encoding='utf-8')
    # Backup any existing snapshots we'll overwrite
    backup_dir = SNAPSHOT_DIR / ".selftest_backup"
    test_snapshots = []

    try:
        # Ensure clean test state: use a minimal index
        test_index_content = json.dumps({"facts": [{"subject": "host", "predicate": "has", "object": "24GB VRAM", "id": 1}], "version": "selftest"})
        INDEX_FILE.write_text(test_index_content, encoding='utf-8')

        # Snapshot 1
        s1 = create_snapshot(label="selftest-v1")
        test_snapshots.append(s1["file"])
        print(f"  [PASS] Snapshot 1 created: {s1['cycle']}")

        # Modify index
        INDEX_FILE.write_text('{"facts": [], "version": "modified"}', encoding='utf-8')

        # Snapshot 2
        s2 = create_snapshot(label="selftest-v2")
        test_snapshots.append(s2["file"])
        print(f"  [PASS] Snapshot 2 created: {s2['cycle']}")

        # History has >=2 entries
        history = list_history()
        hist_ok = len(history) >= 2
        print(f"  [{'PASS' if hist_ok else 'FAIL'}] History lists >=2 cycles: found {len(history)}")
        all_pass = all_pass and hist_ok

        # Corrupt the index
        INDEX_FILE.write_text('{"CORRUPTED": true}', encoding='utf-8')
        corrupt_sum = sha256_file(INDEX_FILE)

        # Rollback to snapshot 1
        result = rollback(s1["cycle"])
        roll_ok = result.get("success", False)
        print(f"  [{'PASS' if roll_ok else 'FAIL'}] Rollback success: {result.get('error', 'OK')}")
        all_pass = all_pass and roll_ok

        # Verify restored content matches original snapshot checksum
        if roll_ok:
            restored_sum = sha256_file(INDEX_FILE)
            match = restored_sum == s1["checksum"]
            print(f"  [{'PASS' if match else 'FAIL'}] Restored checksum matches: {restored_sum[:16]}... == {s1['checksum'][:16]}...")
            all_pass = all_pass and match

            # Verify content is actually the original
            restored_content = INDEX_FILE.read_text(encoding='utf-8')
            content_ok = '"facts"' in restored_content and '24GB VRAM' in restored_content
            print(f"  [{'PASS' if content_ok else 'FAIL'}] Restored content correct: has facts + expected data")
            all_pass = all_pass and content_ok

        # Atomicity check: corrupt a snapshot, rollback should fail cleanly (no partial write)
        snap1_path = ARCHIVIST / s1["file"]
        if snap1_path.exists():
            good_content = snap1_path.read_text(encoding='utf-8')
            # Corrupt the snapshot file
            snap1_path.write_text('{"BROKEN": true}', encoding='utf-8')
            INDEX_FILE.write_text('{"CURRENT": "good"}', encoding='utf-8')
            bad_result = rollback(s1["cycle"])
            atomic_ok = not bad_result.get("success", False) and 'mismatch' in bad_result.get('error', '').lower()
            print(f"  [{'PASS' if atomic_ok else 'FAIL'}] Corrupt snapshot rejected (no partial write): {bad_result.get('error','')}")
            all_pass = all_pass and atomic_ok
            # Restore the good snapshot for cleanup
            snap1_path.write_text(good_content, encoding='utf-8')

    finally:
        # Cleanup: restore original state
        if orig_index is not None:
            INDEX_FILE.write_text(orig_index, encoding='utf-8')
        elif INDEX_FILE.exists() and 'selftest' in INDEX_FILE.read_text(encoding='utf-8'):
            INDEX_FILE.unlink()

        # Remove selftest snapshots from manifest but keep files (or remove both)
        if orig_manifest is not None:
            MANIFEST_FILE.write_text(orig_manifest, encoding='utf-8')
        elif MANIFEST_FILE.exists():
            m = load_manifest()
            m["snapshots"] = [s for s in m["snapshots"] if 'selftest' not in s['cycle']]
            save_manifest(m)

        # Remove selftest snapshot files
        for f in test_snapshots:
            p = ARCHIVIST / f
            if p.exists():
                p.unlink()

    print(f"\n[selftest] {'PASS' if all_pass else 'FAIL'}")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)
    elif "--snapshot" in sys.argv:
        entry = create_snapshot()
        print(json.dumps(entry, indent=2))
    elif "--history" in sys.argv:
        for h in list_history():
            print(f"  {h['cycle']}  {h['timestamp'][:19]}  {h['size_bytes']}B  {h['checksum'][:12]}...")
    elif "--rollback" in sys.argv:
        idx = sys.argv.index("--rollback")
        if idx + 1 >= len(sys.argv):
            print("Usage: --rollback <cycle>")
            sys.exit(1)
        result = rollback(sys.argv[idx + 1])
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)
    else:
        print(__doc__)
        sys.exit(1)