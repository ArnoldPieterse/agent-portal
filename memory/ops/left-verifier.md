Last updated 2026-11-13

# verifier - open goals (split from what_is_left.txt)

verifier | Run a daily portal health check (PID alive, :8099 single listener, /api/git reachable) and log results to memory/ops/.
verifier | Cross-check /api/fleet: assert a status field for all 3 hosts within the 5s refresh window, fail on timeout or missing host.
verifier | Audit .gitignore allowlist after each commit cycle — tracked file count stays ~43; flag drift immediately.
