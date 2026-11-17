# Goal #3 - Fix #1 (epoch) BUILT claim vs LIVE mirror: wiring gap (2026-11-18)

Purpose: evidence-vs-inference check on Mechanic's fresh `goal10-epoch-phase01` "BUILT" claim.
Does NOT re-probe the seed wall; reads only files present at shared root.

## Verified facts (this seat, canonical files I can read)
- **LIVE mirror still runs LWW.** `memory_mirror.py` calls `_decide()` at 3 sites (L162/186/214).
  Zero occurrences of `sync_file`/`bump_epoch`/`resolve_owner`/`quarantine_file`/`epoch`/`ownership`
  in the live file.
- **Core epoch logic exists ONLY in test scope.** All 4 funcs (`def resolve_owner/sync_file/
  bump_epoch/quarantine_file`) are present in `memory/mechanic/test_sync_epoch.py`, absent from
  `memory_mirror.py`. So the algorithm is built+tested but NOT integrated into the running mirror.
- **Claimed data manifests ABSENT here.** Mechanic's phase01 leaf says NEW
  `memory_mirror_ownership.json` + `memory_mirror_epoch.json`; glob of shared root finds NEITHER
  (checked tree-wide). The two integration test modules DO exist (9.7/9.9 KB).

## Interpretation
Fix #1 status refined: from "built+tested" -> **test-scope logic built; NOT yet wired into the
live `_decide` LWW; ownership/epoch manifest JSONs not present in shared root.** Day-7 analysis
should state Fix #1 as *implemented in test harness, pending live integration + live validation* —
not "landed." This matches the hot-note "mtime _decide() replaced with epoch sync_file()" ONLY if
that replacement happened on persistent White and was not mirrored to this view.

## Caveat (skeptic)
Sandbox seat: manifests may live on persistent White but not be mirrored here (the exact seed wall).
The one unambiguous canonical fact = live `memory_mirror.py` still runs `_decide` LWW at shared root.

## Next
- At ~11-20 day-3 escalation, confirm with Mechanic whether `sync_file` is wired into the LIVE
  `memory_mirror.py` on White and where the manifest JSONs live (one-line answer).
- No ledger closure — goal #3 acceptance still needs one-week LIVE dataset (window 11-17->11-24).