"""mirror_canary.py - Canary check for memory mirror sync integrity.
Referenced by: runbook-notes.md
Verifies that pinned files haven't been clobbered by checking SHA hashes.
Usage: python memory/ops/mirror_canary.py [--strict]
Exit codes: 0=all pins intact, 1=drift detected
"""
import hashlib, json, pathlib, sys

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

def main():
    strict = "--strict" in sys.argv
    
    # Read pin manifest if it exists
    pin_file = pathlib.Path("memory/designer/pin_manifest.json")
    if not pin_file.exists():
        print("No pin manifest found - nothing to check.")
        sys.exit(0)
    
    pins = json.loads(pin_file.read_text(encoding="utf-8"))
    issues = []
    
    for pin in pins:
        fpath = pathlib.Path(pin.get("file", ""))
        expected_sha = pin.get("sha12", "")
        if not fpath.exists():
            issues.append(f"MISSING: {fpath}")
            continue
        actual_sha = sha256_file(fpath)
        if actual_sha != expected_sha:
            issues.append(f"DRIFT: {fpath} (expected {expected_sha}, got {actual_sha})")
    
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        sys.exit(1)
    else:
        print(f"All {len(pins)} pins intact.")
        sys.exit(0)

if __name__ == "__main__":
    main()
