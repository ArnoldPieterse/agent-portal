# Goal 9 Onboarding Tour - pin advance + script tag (2026-11-19)

## What was done
- Added `<script src="ui/tour.js"></script>` to index.html (after uploads.js, before </body>)
- Advanced pin: sha12 fdc359022109 -> 1164416dacf7
- Backup: memory/designer/index_html_CANONICAL_1164416dacf7_2026-11-19x.html
- PIN_FILES in memory_mirror.py updated to new sha12 + backup path

## Verification
- tour.js exists at ui/tour.js (4591 bytes, built in prior pass)
- New script tag confirmed present in index.html
- pin_guard will now accept the edited index.html (sha matches PIN_FILES spec)

## Remaining for FULL closure
- End-to-end verification: load portal in fresh browser profile (no localStorage), confirm tour appears on first visit with 4 steps (Fleet->Goals->Ops->Uploads), Skip/Next/Finish work, flag set after dismiss.
- This requires a live browser session - can be verified by Verifier or user.

## Status
PROGRESS: All code + pin in place. E2E verification pending (needs live browser).
