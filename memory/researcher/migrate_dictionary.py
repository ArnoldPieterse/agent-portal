"""MIGRATE dictionary_*.json to confidence-annotated format (Goal #3).

Old format:  term -> [definition, usage]
New format:  term -> {definition, usage, confidence, sources, last_verified}

Run: python memory/researcher/migrate_dictionary.py [--dry-run]
Idempotent: skips entries already in new format.
"""
import json, os, sys, argparse
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [os.path.join(_HERE, "dictionary_core.json"),
         os.path.join(_HERE, "dictionary_project.json")]

def _is_new_format(val):
    return isinstance(val, dict) and "confidence" in val

def migrate_file(path, dry_run=False):
    if not os.path.exists(path):
        print(f"  SKIP (missing): {os.path.basename(path)}")
        return 0
    raw = json.load(open(path, encoding="utf-8"))
    migrated = 0
    for k, v in list(raw.items()):
        if k.startswith("_"):
            continue
        if _is_new_format(v):
            continue  # already migrated
        # old format: [definition, usage]
        definition = str(v[0]) if isinstance(v, (list, tuple)) and len(v) > 0 else ""
        usage = str(v[1]) if isinstance(v, (list, tuple)) and len(v) > 1 else ""
        raw[k] = {
            "definition": definition,
            "usage": usage,
            "confidence": 0.80,  # default for migrated entries
            "sources": [],       # no source URLs known for legacy entries
            "last_verified": str(date.today())
        }
        migrated += 1
    if migrated:
        if dry_run:
            print(f"  DRY-RUN: {os.path.basename(path)} - {migrated} entries would migrate")
        else:
            json.dump(raw, open(path, "w", encoding="utf-8"), indent=2)
            print(f"  MIGRATED: {os.path.basename(path)} - {migrated} entries updated")
    else:
        print(f"  OK (no change): {os.path.basename(path)}")
    return migrated

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    args = ap.parse_args()
    total = 0
    for f in FILES:
        total += migrate_file(f, dry_run=args.dry_run)
    print(f"\nTotal entries migrated: {total}")
    return 0

if __name__ == "__main__":
    sys.exit(main())