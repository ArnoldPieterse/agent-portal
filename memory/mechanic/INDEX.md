# MECHANIC INDEX — staged fixes + probe evidence (newest first).
Last updated: 2026-11-13.

## Entries (keyword -> pointer | use case)
- mirror mtime guard / push_tree abs() fix / skipped_stale audit / apply bundle / hash-verify steps -> memory/mechanic/mirror-mtime-guard-2026-11-13.md   OPS r3 drop-in fix for memory_mirror.py (copy only when src > dst + 0.5s); 7 hunks + md5 verify; apply is White-local (Arnold), no restart needed
- fixed mirror script (staged) -> memory/mechanic/memory_mirror_fixed.py   canonical target md5 c1f4699cb0277368a5a68694f30c5184 (LF, 8669B); NOTE 11-13: mirrored copy at other seats was CRLF 8854B md5 eef3fc9bf9b2c2fc5bf44d37b0801d8f (= +1B/line, pre-final-rewrite) - hash-verify at White before applying
- UNC A/B / TTL vs sleep / C$ denied from Red / hosts awake -> memory/ops/runbook-notes.md   verdict: Route A (reconnect-on-fail) sufficient; probe scripts/results (probe_unc_ab*) NOT yet under memory/ - they will not pull back to White unless moved there
