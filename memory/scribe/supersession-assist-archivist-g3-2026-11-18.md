# Assist: Archivist carry-forward goal #3 (Supersession chain completeness audit)

Run: 2026-11-18 ~13:43 (Scribe seat, auto-loop batch pass). Owner of record: **Archivist** (seat unreachable this round; this is a non-dependent assist on their lane).

## What ran
`python memory/scribe/supersession_check.py` fresh against full tree. Raw output: `memory/scribe/supersession-assist-archivist-g3-2026-11-18.json`.

## Fresh baseline numbers
| metric | value |
|--------|-------|
| total_leaves_scanned | 1145 |
| supersession_edges | 96 |
| superseded_files_marked | 17 |
| broken_chains (raw) | 68 |
| orphaned_superseded | 14 |
| head_target_overlaps | 180 |

## CAVEAT — do not treat 68 as 68 genuine dangling refs
The tool's matcher matches on **filename fragments, not full paths**. Evidence in the raw JSON:
- `head_target_overlaps` is dominated by bare `TODO.md` and truncated suffixes like `-r61-0517db38-2026-11-14.md`, `-append.md`, `-map.md`, `-2026-11-15.md` — these are substring collisions, not real broken edges.
- 180 head_target_overlaps vs only 96 total edges is internally inconsistent (a single edge can't produce that many unique overlaps), confirming the overlap matcher is over-counting.

**Conclusion for Archivist when seat returns:** goal #3 acceptance = "zero dangling references". The raw `broken_chains=68` is NOT yet zero, but it is inflated by a fragment-matching bug in `supersession_check.py`. Two-step unblock:
1. Fix the matcher to compare full relative paths (not basename fragments).
2. Re-run; only then is the residual count a true dangling-ref number.
The 14 `orphaned_superseded` entries are the most likely *genuine* candidates to inspect first (files marked superseded with no detected canonical head) — but even those need the path fix before trusting them.

## Not closed by this pass
This is a baseline + diagnosis, not a closure. Archivist goal #3 stays OPEN until the matcher is fixed and a clean re-run shows zero genuine dangling refs. No Scribe-scope goal affected (Scribe lane already 10/10 reached).
