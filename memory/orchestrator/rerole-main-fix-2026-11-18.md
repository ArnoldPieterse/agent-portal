# rerole_agent.py __main__ fix verified (2026-11-18)

## Bug found + fixed
Entry guard was `if __name__ == "main"` -> main() never ran when script invoked directly.
Fixed to `if __name__ == "__main__"`. One-character class of bug, zero logic change.

## Verification (live agents.json)
- dry-run scribe --new-role archivist: RC 0, correct blurb/persona/tools from template, no files changed.
- unknown agent: RC 2, stderr lists all 8 known ids.
- No git commit attempted (--no-commit).

## Remaining (low-risk)
- Live non-dry-run on a real re-role + confirm portal picks up the new blurb after mirror cycle.
