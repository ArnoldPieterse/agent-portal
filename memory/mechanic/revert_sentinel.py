#!/usr/bin/env python3
"""revert_sentinel.py - Detect + auto-restore mirror-reverted pinned files.

Reads the authoritative pin state from memory_mirror.py PIN_FILES, then
checksum-compares each live file against its canonical backup. On mismatch
(revert), restores from canonical and logs to clobber-events.jsonl.

Usage:
    python memory/mechanic/revert_sentinel.py           # check all pins
    python memory/mechanic/revert_sentinel.py --dry-run # report only, no restore
    python memory/mechanic/revert_sentinel.py --file index.html  # check one file

Exit: 0 = all clean, 1 = revert(s) detected (and restored unless --dry-run)
"""
import hashlib, json, os, sys, time, re

CLOBBER_LOG = "memory/ops/clobber-events.jsonl"
MIRROR_PY = "memory_mirror.py"
DRY_RUN = "--dry-run" in sys.argv

def sha256(path):
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_pins():
    """Parse PIN_FILES from memory_mirror.py. Returns {filename: backup_path}."""
    try:
        content = open(MIRROR_PY).read()
    except FileNotFoundError:
        print(f"[ERROR] {MIRROR_PY} not found")
        return {}
    
    # Extract the PIN_FILES dict block
    m = re.search(r'PIN_FILES\s*=\s*\{', content)
    if not m:
        print("[WARN] PIN_FILES not found in memory_mirror.py")
        return {}
    
    # Find all "filename": {"sha12": "...", "backup": "..."} patterns
    pins = {}
    for fm in re.finditer(r'"([^"]+)"\s*:\s*\{[^}]*"sha12"\s*:\s*"([a-f0-9]+)"[^}]*"backup"\s*:\s*"([^"]+)"', content[m.start():]):
        fname = fm.group(1)
        sha12 = fm.group(2)
        backup = fm.group(3)
        pins[fname] = {"sha12": sha12, "backup": backup}
    return pins

def check_pin(live_path, pin_info):
    """Check one pin against its canonical. Returns (status, detail)."""
    if not os.path.exists(live_path):
        return "MISSING", f"{live_path} does not exist"
    
    live_hash = sha256(live_path)
    expected_sha12 = pin_info["sha12"]
    backup_path = pin_info["backup"]
    
    if not os.path.exists(backup_path):
        return "NO_BACKUP", f"Canonical {backup_path} not found"
    
    # Check: does live file's sha12 (first 12 of sha1) match the pin?
    # Note: PIN_FILES uses first 12 of SHA-1, not SHA-256. Let's use SHA-1 for comparison.
    import hashlib as hl
    h1 = hl.sha1()
    with open(live_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h1.update(chunk)
    live_sha1_12 = h1.hexdigest()[:12]
    
    if live_sha1_12 == expected_sha12:
        return "OK", f"sha12={live_sha1_12} matches pin"
    
    # Also check the backup for reference
    h1b = hl.sha1()
    with open(backup_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h1b.update(chunk)
    backup_sha1_12 = h1b.hexdigest()[:12]
    
    return "REVERTED", f"live_sha12={live_sha1_12} expected={expected_sha12} backup_sha12={backup_sha1_12}"

def restore(live_path, backup_path):
    """Restore live file from canonical backup."""
    with open(backup_path, "rb") as src:
        data = src.read()
    with open(live_path, "wb") as dst:
        dst.write(data)

def log_event(event_type, details):
    """Append to clobber-events.jsonl."""
    os.makedirs(os.path.dirname(CLOBBER_LOG), exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "type": event_type,
        **details,
    }
    with open(CLOBBER_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    pins = load_pins()
    
    if not pins:
        print("[ERROR] No pins loaded. Cannot check.")
        sys.exit(1)
    
    # Filter to single file if requested
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        fname = sys.argv[idx + 1]
        if fname not in pins:
            print(f"[ERROR] {fname} not in PIN_FILES")
            sys.exit(1)
        pins = {fname: pins[fname]}
    
    results = []
    all_ok = True
    
    for live_path, pin_info in sorted(pins.items()):
        status, detail = check_pin(live_path, pin_info)
        results.append({"file": live_path, "status": status, "detail": detail})
        
        if status == "REVERTED":
            all_ok = False
            backup_path = pin_info["backup"]
            if not DRY_RUN and os.path.exists(backup_path):
                restore(live_path, backup_path)
                log_event("auto_restore", {
                    "file": live_path,
                    "restored_from": os.path.basename(backup_path),
                    "expected_sha12": pin_info["sha12"],
                })
                print(f"[RESTORED] {live_path} <- {os.path.basename(backup_path)}")
            else:
                action = "dry_run" if DRY_RUN else "no_backup"
                log_event("revert_detected", {"file": live_path, "detail": detail, "action": action})
                print(f"[REVERT DETECTED] {live_path}: {detail}")
        elif status == "OK":
            print(f"[OK] {live_path}: {detail}")
        else:
            all_ok = False
            print(f"[{status}] {live_path}: {detail}")
    
    summary = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "all_ok": all_ok,
        "files_checked": len(results),
        "results": results,
        "dry_run": DRY_RUN,
    }
    print(f"\nSentinel: {'ALL OK' if all_ok else 'ISSUES FOUND'} ({len(results)} pins checked)")
    
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
