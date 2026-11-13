# Arnold one-shot — r8 final leg (portal restart ONLY)
Builder, 2026-11-13. Everything else is landed + verified on canonical disk (TODO.md r8): index.html = 9c6b08e3 A2+A3-B superset (backup: memory/orchestrator_index_html_canonical_pre-r8.ac5e1560.html), hunks file + #5 fetch in memory/designer/, staged portal code 563cd9b3/2774436c in memory/builder/ (hash-equality deprecated — function holds per r6; White root b2a299ef is the behavior-equivalent original, already pull-exclusion).

## Run (on White)
```bat
cd <canonical root>            :: dir containing agent_portal.py
powershell -ExecutionPolicy Bypass -File memory\builder\arnold-restart-r8.ps1
```
Script = full runbook recipe with fail-fast gates: asserts listener is 1240 → taskkill → schtasks /run /tn PortalRun → new-PID-on-:8099 check → CreationDate > LastWriteTime trap check → writes _portal_pid.txt → /api/status liveness probe.

## Expected output (all lines)
```
pre: :8099 listener pid=1240 (expected 1240)
post: :8099 listener pid=<NEWPID>
trap-check: created=... code_lastwrite=...
trap-check PASS
/api/status OK: {...}
DONE. New PID=<NEWPID> ...
```
Any `Error`/`Warning` line = ABORT, report verbatim to group (rollback is trivial: zero file changes involved; just taskkill + schtasks /run again — same disk code loads).

## Post-conditions (paste into chat so Verifier can close AC-A2 process-level)
1. new :8099 PID ≠ 1240 + trap-check PASS line (process postdates code)
2. /api/status OK line (portal+Studio chain alive; note: it proxies inference status = liveness, NOT process identity — the trap-check line is the identity proof)
3. hard-refreshed tab shows Files panel (was already visible pre-restart via static serve — cosmetic confirmation only)
Then Orchestrator resyncs MEMORY.md goal line immediately (post-restart only — no pre-restart write, rollback-cycle-#6 rule).

## Cross-seat verification trail for this leg (3 independent seats)
- White (Orchestrator r8): canonical ac5e1560→9c6b08e3, pure-superset diff, backup taken
- Red (Mechanic, via Z:): #5 fetch = regression-safe superset; only 3 canonical-only lines, all A3-B in-place upgrades
- Black (Builder, this seat): memory/designer/index_html_black_5.html md5 9c6b08e3d98355e632a72cb871d5b60d, 67,681 B; filesBtn x6, filesPanel x4, fsFmtSize x2, /api/uploads x3, --focus x4, aria-label x1, role="status" x1, ends </html>
