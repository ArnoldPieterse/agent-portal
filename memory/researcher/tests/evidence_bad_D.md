# Evidence: Corrupted Test File (should FAIL validation)
Date: 2026-11-18
Agent: Researcher

## Claim
> Python subprocess.run with check=True raises CalledProcessError on non-zero exit.

### Sources
- https://docs.python.org/3/library/subprocess.html — only ONE source, not enough

### Verification Notes
This file deliberately has insufficient sources to test the validator's failure mode.

## Claim
> The portal mirror sync reverts files that are not pinned.

### Sources
- https://en.wikipedia.org/wiki/Version_control — source 1
- https://en.wikipedia.org/wiki/Hash_function — same domain as source 1 (not independent)

### Verification Notes
Both URLs are from the same domain (wikipedia.org), so they do NOT count as independent.

## Timestamps
- First observation: 2026-11-18T14:00
- Re-verification: 2026-11-17T09:30  <-- DELIBERATELY EARLIER (violates monotonicity)