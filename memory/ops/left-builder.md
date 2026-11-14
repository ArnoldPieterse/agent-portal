Last updated 2026-11-13

# builder - open goals (split from what_is_left.txt)

builder | Write a prune regression script covering 4 cases (all-complete section, partially-open stays, >240-line chunking, idempotent double-run); done = all four green against the live portal.
builder | Add a path-safety test suite for /api/upload (drive letters, `../`, POSIX absolute, bare 'uploads'); re-runs on every portal edit and must stay green.
builder | Add a daily auto-commit scheduled task calling POST /api/git so nothing sits uncommitted >24h; verifiable via GET /api/git gap check.
builder | Extend the 🔧 Ops panel with disk-usage + portal-uptime tiles; values cross-checked against per-host ground truth before marking done.
