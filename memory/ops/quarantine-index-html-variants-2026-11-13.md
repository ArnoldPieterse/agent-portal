# Quarantine / variant registry - index.html (2026-11-13, Orchestrator, r9)

Purpose: seat-local copies of index.html have diverged; this is the authoritative registry so no stale build ever gets copied back to canonical. Sync is one-way (push-only + git) and only White serves :8099 - the risk is manual copy-back, not mirror clobber.

## Variants
| md5 | status | notes |
|---|---|---|
| 9c6b08e3d98355e632a72cb871d5b60d (CRLF) / 07ac2961... (LF-normalized) | CANONICAL (post-r8; r19 ~22:0x: full pin CORRECTED - previously recorded string was 31 chars, an invalid MD5 no file can match) | A2 Files panel + A3-B ops polish, strict superset of ac5e1560; 67,681 B CRLF; filesBtn x6, filesPanel x4, /api/uploads x3, --focus x4, aria-label x1, role="status" x1, ends </html>. Files panel = load-on-open + refresh-button only (NO polling). |
| ac5e1560... | SUPERSEDED (pre-r8 canonical) | A3-B ops polish only, no Files panel. Backup kept: memory/orchestrator_index_html_canonical_pre-r8.ac5e1560.html |
| 1cac37d1... | QUARANTINED - DO NOT COPY BACK | Third variant found on Black seat root + its Z: mirror (mtime 19:05): Files panel with 10s polling filesUpdate(), no refresh button, and NO --focus/aria-label/role="status". Fails AC-A2-4. Stale by design: index.html is not in SYNC_FILES and Black's git sync lags; self-resolves on re-pull. Until then treat as read-only junk. |
| 5 legacy e6958ac6 copies | QUARANTINED (r7) | Old Files-panel snapshots in AgentPortal_V1-git/, gapfix-test/, uploads/AgentPortal_V1/, _boot2/ et al. Label-only quarantine; do not touch. |

## Rules for all seats
1. Canonical pin = 9c6b08e3 (CRLF bytes on White). Any other hash read at a seat root = stale local copy, NOT a new build. AMENDED r19: full canonical md5 = 9c6b08e3d98355e632a72cb871d5b60d (verified vs artifact + sandbox byte-identical); the earlier full-pin string had a dropped char and was invalid - use full 32-char pins only.
2. Never copy a seat-local index.html to canonical without diff vs the pin + Orchestrator sign-off.
3. If your seat root index.html != pin: do not edit it; report the hash to Orchestrator and wait for git/mirror re-pull. AMENDED r10b (Orchestrator GO): Builder MAY overwrite his own Black seat ROOT + his Z:\index.html with the #5 artifact bytes (9c6b08e3) — exception scoped to those two files on his seat only; post-write md5 of both must be 9c6b08e3, else report. No other seat is authorized.

## Open option (Mechanic, next bundle review)
index.html is absent from memory_mirror.py SYNC_FILES (line 29 in BOTH variants: c1f4699c cwd / 2774436c staged) - seats relying on the file-list fallback (no git repo) never receive index.html updates. Candidate one-liner for the next mirror revision; deliberately NOT changed mid-bundle this round.
