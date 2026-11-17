"""
Unit tests for mirror sync epoch logic (Goal #10, Phase 1).

Tests the core functions from memory/researcher/sync-semantics-spec-2026-11-17.md:
  T1-T3: resolve_owner()
  T4-T9: sync_file() decision matrix
  T10:   epoch monotonicity
  T11:   quarantine file placement
  T12:   atomic manifest write

Run: python memory/mechanic/test_sync_epoch.py
No network required. Uses tmp dirs for filesystem tests.
"""
import json, os, shutil, tempfile, hashlib
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # project root
OWNERSHIP_FILE = HERE / "memory_mirror_ownership.json"
EPOCH_FILE = HERE / "memory_mirror_epoch.json"

# --- Core functions (extracted from spec, will be integrated into memory_mirror.py in Phase 2) ---

def load_ownership_map(path=OWNERSHIP_FILE):
    with open(path) as f:
        return json.load(f)

def resolve_owner(rel_path, ownership_map):
    """Longest-prefix match; default_owner if no rule matches."""
    best = None
    for rule in ownership_map["rules"]:
        if rel_path.startswith(rule["prefix"]):
            if best is None or len(rule["prefix"]) > len(best["prefix"]):
                best = rule
    return best["owner"] if best else ownership_map["default_owner"]

def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_epoch_manifest(path=EPOCH_FILE):
    with open(path) as f:
        return json.load(f)

def save_epoch_manifest(manifest, path=EPOCH_FILE):
    """Atomic write: tmp + rename."""
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp, str(path))

def bump_epoch(manifest, rel_path, seat, ownership_map):
    entry = manifest["entries"].get(rel_path, {"epoch": 0})
    new_epoch = entry["epoch"] + 1
    manifest["entries"][rel_path] = {
        "owner": resolve_owner(rel_path, ownership_map),
        "epoch": new_epoch,
        "last_writer": seat,
        "ts": datetime.now().isoformat(timespec="seconds")
    }
    return new_epoch

def sync_file(sp, dp, rel_path, owner_seat, local_seat, epoch_manifest, direction, remote_seat=None):
    """
    Decision function replacing _decide() LWW.
    Returns (action, meta) tuple.
    """
    entry = epoch_manifest["entries"].get(rel_path)
    owner_epoch = entry["epoch"] if entry else 0

    # Case 1: dest doesn't exist -> copy (new file)
    if not os.path.exists(dp):
        return "copy", {"reason": "new", "new_epoch": owner_epoch + 1}

    # Case 2: hashes equal -> no-op
    hs, hd = _md5(sp), _md5(dp)
    if hs == hd:
        return "skip_same", {}

    # Direction-specific logic (Case 4 from spec)
    if direction == "push":
        if owner_seat == local_seat:
            return "copy", {"reason": "owner_push", "new_epoch": owner_epoch + 1}
        else:
            return "skip_foreign", {"reason": f"owned by {owner_seat}, not pushing from {local_seat}"}
    else:  # pull
        if owner_seat == remote_seat:
            return "copy", {"reason": "owner_pull", "new_epoch": owner_epoch + 1}
        elif owner_seat == local_seat:
            return "quarantine", {"reason": f"remote {remote_seat} modified {local_seat}-owned file"}
        else:
            return "quarantine", {"reason": f"ambiguous ownership: owner={owner_seat}, remote={remote_seat}"}

def quarantine_file(sp, rel_path, source_seat, reason, quarantine_root):
    """Move foreign write to quarantine inbox with provenance metadata."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    qdir = os.path.join(quarantine_root, f"{ts}_{source_seat}")
    dest = os.path.join(qdir, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(sp, dest)
    meta = {
        "source_seat": source_seat,
        "original_path": rel_path,
        "detected_at": datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "md5": _md5(sp)
    }
    with open(os.path.join(qdir, "_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    return qdir

# --- Test harness ---

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")

def run_tests():
    global PASS, FAIL
    om = load_ownership_map()
    tmpdir = tempfile.mkdtemp(prefix="sync_epoch_test_")
    try:
        # T1: resolve_owner default
        check("T1 resolve_owner default", resolve_owner("TODO.md", om) == "White",
              f"got {resolve_owner('TODO.md', om)}")

        # T2: resolve_owner lane
        check("T2 resolve_owner lane", resolve_owner("memory/researcher/x.md", om) == "Researcher",
              f"got {resolve_owner('memory/researcher/x.md', om)}")

        # T3: resolve_owner longest-prefix
        # Add a nested rule to test longest-prefix
        om_nested = dict(om)
        om_nested["rules"] = list(om["rules"]) + [{"prefix": "memory/researcher/sub/", "owner": "SubOwner"}]
        check("T3 resolve_owner longest-prefix",
              resolve_owner("memory/researcher/sub/y.md", om_nested) == "SubOwner",
              f"got {resolve_owner('memory/researcher/sub/y.md', om_nested)}")

        # T4: New file push (dest doesn't exist)
        sp = os.path.join(tmpdir, "src.txt")
        dp = os.path.join(tmpdir, "dst.txt")
        with open(sp, "w") as f: f.write("hello")
        manifest = {"version": 1, "entries": {}}
        action, meta = sync_file(sp, dp, "TODO.md", "White", "White", manifest, direction="push")
        check("T4 new file push", action == "copy" and meta["new_epoch"] == 1,
              f"got ({action}, {meta})")

        # T5: Same hash skip
        with open(dp, "w") as f: f.write("hello")
        action, meta = sync_file(sp, dp, "TODO.md", "White", "White", manifest, direction="push")
        check("T5 same hash skip", action == "skip_same", f"got {action}")

        # T6: White-owned push (hash differs)
        with open(sp, "w") as f: f.write("updated content")
        manifest["entries"]["TODO.md"] = {"owner": "White", "epoch": 5, "last_writer": "White", "ts": "2026-11-18T00:00:00"}
        action, meta = sync_file(sp, dp, "TODO.md", "White", "White", manifest, direction="push")
        check("T6 White-owned push", action == "copy" and meta["new_epoch"] == 6,
              f"got ({action}, {meta})")

        # T7: Foreign push skipped
        action, meta = sync_file(sp, dp, "memory/researcher/x.md", "Researcher", "White", manifest, direction="push")
        check("T7 foreign push skipped", action == "skip_foreign",
              f"got {action}")

        # T8: Owner pull accepted
        sp2 = os.path.join(tmpdir, "remote_file.txt")
        dp2 = os.path.join(tmpdir, "local_file.txt")
        with open(sp2, "w") as f: f.write("remote data")
        with open(dp2, "w") as f: f.write("stale local")
        action, meta = sync_file(sp2, dp2, "memory/mechanic/y.md", "Mechanic", "White", manifest, direction="pull", remote_seat="Mechanic")
        check("T8 owner pull accepted", action == "copy" and meta["new_epoch"] == 1,
              f"got ({action}, {meta})")

        # T9: Foreign pull quarantined (Red modifies White-owned file)
        sp3 = os.path.join(tmpdir, "foreign.txt")
        dp3 = os.path.join(tmpdir, "white_owned.txt")
        with open(sp3, "w") as f: f.write("I am foreign")
        with open(dp3, "w") as f: f.write("original white content")
        action, meta = sync_file(sp3, dp3, "TODO.md", "White", "White", manifest, direction="pull", remote_seat="Red")
        check("T9 foreign pull quarantined", action == "quarantine",
              f"got {action}")

        # T10: Epoch monotonicity
        m2 = {"version": 1, "entries": {}}
        e1 = bump_epoch(m2, "TODO.md", "White", om)
        e2 = bump_epoch(m2, "TODO.md", "White", om)
        e3 = bump_epoch(m2, "TODO.md", "White", om)
        check("T10 epoch monotonicity", (e1, e2, e3) == (1, 2, 3),
              f"got ({e1}, {e2}, {e3})")

        # T11: Quarantine file lands correctly
        qroot = os.path.join(tmpdir, "quarantine")
        os.makedirs(qroot, exist_ok=True)
        qdir = quarantine_file(sp3, "TODO.md", "Red", "test foreign write", qroot)
        # Check the file exists somewhere in qdir
        found = False
        for root, dirs, files in os.walk(qdir):
            if "_meta.json" in files:
                with open(os.path.join(root, "_meta.json")) as f:
                    meta_q = json.load(f)
                if meta_q["original_path"] == "TODO.md" and meta_q["source_seat"] == "Red":
                    found = True
        check("T11 quarantine file lands", found, f"quarantine dir: {qdir}")

        # T12: Atomic manifest write (no partial JSON)
        ep_path = os.path.join(tmpdir, "epoch_test.json")
        m3 = {"version": 1, "entries": {"a.md": {"owner": "White", "epoch": 1, "last_writer": "White", "ts": "now"}}}
        save_epoch_manifest(m3, ep_path)
        # Verify it's valid JSON and no .tmp left behind
        with open(ep_path) as f:
            loaded = json.load(f)
        tmp_exists = os.path.exists(str(ep_path) + ".tmp")
        check("T12 atomic manifest write", loaded == m3 and not tmp_exists,
              f"loaded={loaded}, tmp_exists={tmp_exists}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\n{'='*50}")
    print(f"RESULTS: {PASS}/{PASS+FAIL} PASS, {FAIL} FAIL")
    if FAIL == 0:
        print("ALL TESTS PASSED")
    return FAIL == 0

if __name__ == "__main__":
    ok = run_tests()
    raise SystemExit(0 if ok else 1)