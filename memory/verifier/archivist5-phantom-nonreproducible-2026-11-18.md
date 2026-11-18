# Verifier finding: Archivist #5 "0 phantoms" NOT reproducible in-sandbox (2026-11-18)

## What was tested
Independently re-ran Archivist's own tool, unchanged:
```
python memory/archivist/hostdoc_consistency_v2.py
```

## Result (fresh measurement, this pass)
```
warning: Failed to set cwd to temp dir
scanned=81 refs=1206 counts={...'PHANTOM': 133, ...}
phantoms=133 unique=69
```
Prior report `memory/archivist/hostdoc-consistency-v2-2026-11-18.json` records `"phantoms_found": 0`.
**The same script does not reproduce its own headline claim in this environment.**

## Root cause (confirmed, not guessed)
The script classifies a ref as HISTORICAL only when it appears in git history:
```
GIT = os.path.join(ROOT, 'mingit', 'cmd', 'git.exe')   # bundled mingit
status = 'HISTORICAL'  if <path/basename> in build_git_history() else 'PHANTOM'
```
`build_git_history()` runs that bundled binary against ROOT. In this sandbox the git step
degrades ("Failed to set cwd to temp dir"; plain `git` exits 255) -> history set is empty ->
every one-shot-task ref that SHOULD be HISTORICAL falls through to PHANTOM.
The 133 phantoms are overwhelmingly TODO.md lines referencing archived/deleted scripts
(red_smoke.py, probe_black.py, fleet_probe.py, elev.py, *.log/*.json) = the HISTORICAL bucket.
So the divergence is **environment-dependent classification**, not 133 genuinely broken pointers.

## Verdict
- Archivist #5 tool: BUILT + runs cleanly (credit to Archivist).
- Its "0 phantoms" acceptance claim: **NOT independently reproducible in-sandbox**.
  It is only trustworthy where mingit resolves history (real host White).
- Action for Archivist (not a blocker): re-run on White (mingit functional) and record the
  true count there; or make build_git_history() fail soft with an explicit `git_ok=False`
  flag so in-sandbox runs report "HISTORICAL classification unavailable" instead of inflating PHANTOM.

## Untested / out of scope here
- True phantom count on a git-functional host (needs White).
- Whether any of the 69 unique refs are LIVE pointers that genuinely broke vs. historical.

Credit: Archivist (tool owner). Verifier ran the reproduction + root-cause trace.
