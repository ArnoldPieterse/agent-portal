# Test report - new ops processes (Verifier goal #10)

## 1. /api/todo/prune - PASS
Live dry_run returned 200 with real data (would_move=1, part files listed).
Fixture regression memory/builder/prune_regression.py: ALL PASS (4/4), rc=0.
Evidence: memory/verifier/prune-e2e-2026-11-15.md

## 2. Git integration - PASS
GET /api/git -> repo=true, live status. POST commit -> [main 05af0c1] committed=True,
working tree clean afterwards (changed=0). Evidence: memory/verifier/git-evidence-2026-11-15.md

## 3. Upload round-trip - PASS (Builder #1 acceptance)
POST /api/upload 201 -> listed in GET /api/uploads -> deleted -> gone.
Evidence: memory/builder/uploads-panel-verify-2026-11-15.md

## 4. Endpoint smoke sweep - PASS
35 distinct /api/* routes; every GET-able route answered 2xx (404s = POST-only/param-routed).
Evidence: memory/verifier/smoke-sweep-2026-11-15.md

## Not closed (honest gaps)
- Verifier #9: only prune + git of the 5 regression points have fresh evidence.
- Black UD-Q4_K_S load: blocked by Studio API change (raw paths rejected for
  transformers models). Q8_0 restored; see memory/ops/black-reload-2026-11-15.md.
