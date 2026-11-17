#!/usr/bin/env python3
"""
manifest.py - SHA256 hash manifest generator + verifier for UI baseline screenshots.

USAGE:
  python manifest.py              # generate/update manifest.json from all PNGs here
  python manifest.py --verify     # verify existing PNGs match manifest (exit 0=pass, 1=fail)
  python manifest.py --list       # print current manifest contents
"""
import os, sys, json, hashlib, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(BASE, "manifest.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate():
    """Scan BASE for .png files, write manifest.json."""
    entries = {}
    pngs = sorted(f for f in os.listdir(BASE) if f.endswith(".png"))
    for fn in pngs:
        full = os.path.join(BASE, fn)
        size = os.path.getsize(full)
        digest = sha256_file(full)
        entries[fn] = {"sha256": digest, "bytes": size}

    manifest = {
        "generated": datetime.datetime.now().isoformat(),
        "file_count": len(pngs),
        "closure_threshold": 8,
        "meets_closure": len(pngs) >= 8,
        "files": entries,
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)

    status = "CLOSURE MET" if manifest["meets_closure"] else f"NOT MET ({len(pngs)}/8)"
    print(f"[manifest] {len(pngs)} PNGs hashed -> {os.path.basename(MANIFEST)}")
    print(f"[closure]   {status}")
    return 0


def verify():
    """Check all PNGs in BASE match their manifest entries."""
    if not os.path.isfile(MANIFEST):
        print("[verify] FAIL: manifest.json not found. Run without --verify first.")
        return 1
    with open(MANIFEST) as f:
        manifest = json.load(f)

    failures = []
    for fn, entry in manifest["files"].items():
        full = os.path.join(BASE, fn)
        if not os.path.isfile(full):
            failures.append(f"MISSING: {fn}")
            continue
        actual = sha256_file(full)
        if actual != entry["sha256"]:
            failures.append(f"MISMATCH: {fn} (expected {entry['sha256'][:12]}..., got {actual[:12]}...)")

    # Check for new files not in manifest
    current = set(f for f in os.listdir(BASE) if f.endswith(".png"))
    tracked = set(manifest["files"].keys())
    new_files = current - tracked
    for fn in sorted(new_files):
        failures.append(f"UNTRACKED: {fn} (new file not in manifest)")

    if failures:
        print(f"[verify] FAIL ({len(failures)} issues):")
        for f2 in failures:
            print(f"  - {f2}")
        return 1
    else:
        print(f"[verify] PASS: all {len(manifest['files'])} files match manifest.")
        return 0


def list_manifest():
    if not os.path.isfile(MANIFEST):
        print("[list] No manifest.json found. Run without --list to generate.")
        return 0
    with open(MANIFEST) as f:
        m = json.load(f)
    print(f"Baseline manifest: {m['file_count']} files, generated {m['generated']}")
    print(f"Closure threshold: {m['closure_threshold']} | Met: {m['meets_closure']}")
    print("-" * 60)
    for fn in sorted(m["files"]):
        e = m["files"][fn]
        print(f"  {fn:<45} {e['bytes']:>8} B  sha256={e['sha256'][:16]}...")
    return 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    elif "--list" in sys.argv:
        sys.exit(list_manifest())
    else:
        sys.exit(generate())
