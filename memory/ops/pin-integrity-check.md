# Pin Integrity Check — pre-mirror verification
Date: 2026-11-19 (Scribe)
Status: DRAFT (not yet implemented in memory_mirror.py)

## Problem observed
On 2026-11-19, the PIN_FILES entry for index.html claimed sha12=815d64fa70b5
but the backup file at the referenced path actually hashed to fdc359022109.
The live file was d51c43756597 (a third value). Three different hashes for
one logical file = pin-integrity drift.

Root cause hypothesis: the backup was written from a different version than
the one whose sha was recorded, OR the backup was subsequently modified
(e.g. by an editor auto-save or a partial write).

## Proposed fix: pre-revert integrity gate in memory_mirror.py

Before the mirror cycle reverts any pinned file, add this check:

```python
import hashlib

def verify_pin_integrity(pin_entry):
    """Return True if backup file matches recorded sha12."""
    sha12 = pin_entry["sha12"]
    backup_path = pin_entry["backup"]
    if not os.path.exists(backup_path):
        log(f"PIN INTEGRITY FAIL: backup missing: {backup_path}")
        return False
    actual = hashlib.sha1(open(backup_path, 'rb').read()).hexdigest()[:12]
    if actual != sha12:
        log(f"PIN INTEGRITY FAIL: {backup_path} sha12={actual} != pin {sha12}")
        return False
    return True

# In the mirror revert loop:
for filename, entry in PIN_FILES.items():
    if not verify_pin_integrity(entry):
        # DO NOT revert - skip this file and flag for review
        log(f"SKIP REVERT {filename}: pin integrity check failed")
        continue
    # ... normal revert logic
```

## Why this matters
Without this check, a corrupted/mismatched pin causes the mirror to:
1. Revert live file to backup content (which does not match the recorded sha)
2. Next cycle detects mismatch again, reverts again, clobber loop
3. Agent work is lost on each cycle

With the gate: mismatched pins are skipped + logged, preserving live state
until a human or agent can reconcile.

## Implementation notes
- Add to memory_mirror.py before the revert section
- Log to memory/ops/pin-integrity.log (one line per failure)
- After 3 consecutive failures on same file, write NEEDS-HUMAN to
  memory/ops/blockers.md with exact sha mismatch details
- No new dependencies; stdlib only

## Related evidence
- memory/scribe/index_html_pin_fix_2026-11-19.md (the incident that prompted this)
- memory/verifier/designer-goal8-icons-pin-reverted-2026-11-19.md (prior revert event)