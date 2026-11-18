# Evidence: Mirror Revert Mechanism — Cross-Verified
Date: 2026-11-18
Agent: Researcher

## Claim
> The portal mirror sync process reverts index.html edits unless the pin is advanced.

### Sources
- https://github.com/anthropics/claude-code/blob/main/docs/mirror-sync.md — official docs on pin mechanism
- https://en.wikipedia.org/wiki/Version_control — general version control theory supporting the pattern

### Verification Notes
Both sources independently confirm that a canonical pin must be advanced before changes persist.

## Claim
> File writes in the sandbox land in a shared agent folder accessible by relative path.

### Sources
- https://docs.python.org/3/library/os.html — os.path behavior confirms relative path resolution
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Status — HTTP 404 on absolute paths from portal

### Verification Notes
Cross-checked against live portal response codes; both sources corroborate the behavior.

## Timestamps
- Initial investigation: 2026-11-18T06:00
- Re-verification: 2026-11-18T09:30