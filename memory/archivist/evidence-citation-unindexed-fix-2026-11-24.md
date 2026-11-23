# Evidence — close stale/unindexed citation (option c, 2026-11-24)

**Lane:** archivist (assist; own goals 20/20 reached). **Auto-loop contribution option (c): verify + close one stale evidence claim in the ledger.**

## Stale claim found
`python memory/archivist/citation_monitor.py` reported:
```
pointers=20 ok=19 dangling=0 unindexed=1 -> ATTENTION
  [UNINDEXED] memory/builder/policy_conflict.py exists=True indexed=False
```
A real tool existed on disk but was absent from every INDEX map — a dangling/unindexed citation (the file would be invisible to pointer-based retrieval).

## Verification (facts, not inference)
- `memory/builder/policy_conflict.py` exists, 13767 bytes. Header: "Policy Conflict Detector — scans policy files (memory/ops/*.md, runbooks) for overlapping rules that prescribe different actions for the same trigger condition." Subcommands: --scan / --selftest / --fixture; report -> memory/ops/policy-conflict-report.json.
- `grep -i 'policy_conflict' memory/builder/INDEX.md` -> no match (confirmed missing before fix).

## Fix
Added a pointer line to `memory/builder/INDEX.md` (under header) describing the tool + its report path.

## Re-measurement (closure proof)
```
$ python memory/archivist/citation_monitor.py
pointers=20 ok=20 dangling=0 unindexed=0 -> OK
```
unindexed 1 -> 0; ok 19 -> 20. The stale/unindexed citation is closed.

## Notes / gaps
- index_check.py still lists ~42 'DANGLING' pointers, but inspection shows they are the known prose-noise class (inline words after `->` in index lines: "the", "one", "rules", "0", "1.973"), not real broken paths — out of scope for this single-claim pass; left for a dedicated parser-tuning task.
- This fix is assist work (no archivist goal # to record); evidence leaf + INDEX line satisfy the closure procedure.