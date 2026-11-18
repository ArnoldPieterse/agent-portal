"""Verify portal source files against the baseline manifest.
Exit 0 = no changes detected, Exit 1 = drift found."""
import hashlib, json, os, sys

MANIFEST = os.path.join(os.path.dirname(__file__), "MANIFEST_SOURCE.json")

def main():
    with open(MANIFEST) as f:
        m = json.load(f)
    
    drift = []
    for entry in m["files"]:
        fpath = entry["file"]
        if not os.path.exists(fpath):
            drift.append(f"  MISSING: {fpath}")
            continue
        with open(fpath, 'rb') as fh:
            cur = hashlib.sha256(fh.read()).hexdigest()
        if cur != entry["sha256"]:
            drift.append(f"  CHANGED: {fpath} (baseline={entry['sha256'][:12]}... current={cur[:12]}...)")
    
    if drift:
        print("DRIFT DETECTED:")
        print("\n".join(drift))
        sys.exit(1)
    else:
        print(f"OK: all {len(m['files'])} source files match baseline.")
        sys.exit(0)

if __name__ == "__main__":
    main()
