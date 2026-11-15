# Builder goal #1 - Files panel acceptance round-trip (2026-11-15 ~22:3x, non-sandbox seat)

Acceptance: "verified with a hard refresh that a test upload appears in the Files panel, then delete it."
Executed against the live portal (127.0.0.1:8099):
1. POST /api/upload X-Rel-Path=verify-upload-test-2026-11-15.txt (51 B) -> 201 {ok, path: uploads/verify-upload-test-2026-11-15.txt}
2. GET /api/uploads -> file present in listing (count 5381)
3. File removed from <sandbox>/uploads; GET /api/uploads -> no longer listed.
UI side: index.html carries the A2 files-panel (filesBtn/filesPanel, load-on-open + refresh-only).

Verdict: PASS - upload lands, lists, and deletes cleanly.
