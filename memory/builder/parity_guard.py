#!/usr/bin/env python3
"""
parity_guard.py - Sandbox <-> shared-root parity check.

Hashes an allowlist of files in the Studio sandbox root and compares
against a known-good baseline snapshot. Mismatches logged to
memory/ops/clobber-events.jsonl.

Usage:
    python memory/builder/parity_guard.py            # check + report
    python memory/builder/parity_guard.py --record   # save new baseline
    python memory/builder/parity_guard.py --verbose  # show all diffs
"""
import hashlib, json, os, sys, time

BASELINE_FILE = "memory/builder/parity-baseline.json"
EVENTS_FILE = "memory/ops/clobber-events.jsonl"

# Allowlist: files that must stay in sync between sandbox and shared root.
# These are the critical project files where a clobber would cause data loss.
ALLOWLIST = [
    "agent_portal.py",
    "evolution.py",
    "index.html",
    "memory/INDEX.md",
    "memory/goals/builder.md",
    "memory/goals/designer.md",
    "memory/goals/archivist.md",
    "memory/goals/scribe.md",
    "memory/goals/mechanic.md",
    "memory/goals/verifier.md",
    "TODO.md",
]


def sha256_file(path):
    """Compute SHA-256 of a file, return hex digest or None if missing."""
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_current_state():
    """Hash all allowlist files that exist."""
    state = {}
    for rel in ALLOWLIST:
        digest = sha256_file(rel)
        if digest is not None:
            state[rel] = {"sha256": digest, "size": os.path.getsize(rel)}
    return state


def load_baseline():
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    return None


def record_baseline():
    """Save current state as the new baseline."""
    state = get_current_state()
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump({
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "files": state
        }, f, indent=2)
    print(f"Baseline recorded: {len(state)} files -> {BASELINE_FILE}")


def check(verbose=False):
    """Compare current state against baseline. Return (ok, mismatches)."""
    baseline = load_baseline()
    if not baseline:
        print("[WARN] No baseline found. Run with --record first.")
        return True, []

    current = get_current_state()
    baseline_files = baseline.get("files", {})
    mismatches = []

    # Check for changes
    for rel in sorted(set(list(baseline_files.keys()) + list(current.keys()))):
        b = baseline_files.get(rel)
        c = current.get(rel)

        if b and not c:
            mismatches.append({"file": rel, "type": "DELETED", "baseline_sha": b["sha256"][:12]})
        elif c and not b:
            mismatches.append({"file": rel, "type": "NEW", "current_sha": c["sha256"][:12]})
        elif b and c and b["sha256"] != c["sha256"]:
            mismatches.append({
                "file": rel,
                "type": "MODIFIED",
                "baseline_sha": b["sha256"][:12],
                "current_sha": c["sha256"][:12],
                "baseline_size": b["size"],
                "current_size": c["size"]
            })

    if verbose:
        print(f"\nFiles checked: {len(current)} current, {len(baseline_files)} baseline")
        for rel in sorted(current.keys()):
            status = "OK" if rel not in [m['file'] for m in mismatches] else "MISMATCH"
            print(f"  [{status:8s}] {rel}")

    # Log events
    if mismatches:
        os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
        with open(EVENTS_FILE, "a") as f:
            for m in mismatches:
                m["detected_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                m["source"] = "parity_guard"
                f.write(json.dumps(m) + "\n")
        print(f"\n[ALERT] {len(mismatches)} mismatches logged to {EVENTS_FILE}")

    ok = len(mismatches) == 0
    return ok, mismatches


if __name__ == "__main__":
    if "--record" in sys.argv:
        record_baseline()
    elif "--verbose" in sys.argv:
        ok, m = check(verbose=True)
        print(f"\n=== RESULT: {'PARITY OK' if ok else f'{len(m)} MISMATCHES'} ===")
        sys.exit(0 if ok else 1)
    else:
        ok, m = check()
        if ok:
            print("Parity check: OK (all allowlist files match baseline)")
        else:
            print(f"Parity check: {len(m)} MISMATCHES")
            for mm in m:
                print(f"  [{mm['type']}] {mm['file']}")
        sys.exit(0 if ok else 1)
