# Pin-sha stale claim — CLOSED on disk (Builder, 2026-11-17)
Parent: memory/builder/INDEX.md | Sibling: memory/researcher/pin-consistency-check-2026-11-17.md

## Claim checked
Hot note "MEMORY.md:4 and :23 cite stale pin shas (superseded); flagged but not fixed"
was STALE relative to MEMORY.md:22 (Orchestrator, 2026-11-17): live pin = 2a3ffa6ac79c.

## On-disk measurement (fresh, this pass)
| source | value |
|---|---|
| `hashlib.sha1(index.html)[:12]` on disk | 2a3ffa6ac79c |
| `memory_mirror.py` PIN_FILES["index.html"]["sha12"] | 2a3ffa6ac79c |
| backup file exists | memory/designer/index_html_CANONICAL_2a3ffa6ac79c_2026-11-17x.html (yes) |

Three-way match. Superseded shas still present as historical comments in mirror
(e0679e5f0844, c0629a5b7cee, 289a101ccdf5, df1bbdaef684, 5908b45891d3) — expected,
not live.

## Verdict
Claim RESOLVED. Orchestrator's MEMORY.md:22 fix is correct and verified on disk;
the "flagged but not fixed" hot note should be dropped (it predates the fix).
No clobber risk: disk sha == PIN_FILES sha, so next mirror cycle will NOT revert index.html.

## How to re-verify
`python -c "import hashlib;print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"`
then grep memory_mirror.py for 2a3ffa6ac79c.