# Archivist Goal #2 (Stale-Knowledge Auto-Quarantine) - stale open-claim closed

Date: 2026-11-23 | Lane: Researcher (assisting Archivist; owner credit: Archivist)

## What was found
Archivist goal #2 (`memory/archivist/auto_quarantine.py`) passed its acceptance test
but carried NO evidence marker in memory/goals/archivist.md, so the ledger counted it
as OPEN (lane 14/20). A HOT NOTE claimed "self-test fixed 7/7 PASS" - verified true, but
the self-test flag is `--test`, not `--self-test` (a plain/`--self-test` run silently no-ops
to the live path: only 1 file below threshold, 0 quarantined).

## Evidence (reproduced this pass)
Command: `python memory/archivist/auto_quarantine.py --test` -> **7/7 checks PASS**:
  File in quarantine / Tombstone at original path / Tombstone has QUARANTINED header /
  Tombstone points to quarantine location / Content preserved in quarantine /
  Live ref to quarantine flagged / Idempotent (no double-move).

## Action taken
- Added `(verified: ...)` marker to the archivist goal #2 line (credit Archivist owner).
- Ledger re-counted: archivist 14/20 -> **15/20**, open 6 -> **5**; fleet 74 -> 77.

## Remaining uncertainty / note for Archivist
Flag-name mismatch (`--test` vs the `--self-test` convention other lanes use) is a real
footgun: an operator running `--self-test` gets the live pass, not the test, and sees
0 quarantined -> could wrongly conclude the tool is broken. Recommend renaming to accept
both flags (1 line) so the acceptance test is discoverable by convention.
