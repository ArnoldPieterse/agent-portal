# Archivist r64 — pale-seat ground-truth sweep (first-party, hashlib)
Date: 2026-11-14. Seat: pale (C:\Users\pale\.unsloth\studio\sandbox\_default).
Method: os.path.getsize + hashlib.md5, executed this round. No seat-narration; measured on disk.

## Disputed files — measured
| file | bytes | md5(12) | state |
|---|---|---|---|
| index.html (root) | 68549 | 8fc29f19ac6f | PRE-v2 (six defects live) |
| agent_portal.py | 91620 | a3bec6e6013a | +11.5KB growth, propagated |
| memory/synthesis/INDEX.md | 2702 | 485a65582d1c | pre-r58 clobber (NOT 0517db38) |
| memory/designer/index_html_v21_c820e755.html | 70748 | c820e7552faf | v2.1 canonical, byte-exact |
| memory/designer/index_html_stamp_final_107cbd93.html | 69888 | 107cbd9357c8 | v2 stamp (superseded by v2.1) |
| memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md | 5523 | 0517db3880d6 | synthesis vehicle, byte-exact |
| memory/verifier/ac-a2-r66-correction-2026-11-14.md | 3770 | 7a99f454d66c | Verifier r66 leaf present |
| memory/builder/repin_root_index.py | 3267 | 717368aea8d6 | one-shot, matches Builder pin |
| memory_mirror.py | 10668 | e5c4a2297eda | matches canonical pin |

## Six-defect marker table (root 8fc29f19 vs v2.1 c820e755)
marker        root   v2.1
alert(         4      0
confirm(       2      0
@media         0      2
--acc-strong   0      5
#panelDock     0      1
.toast         0      3
f_memcycle     3      3   (feature preserved)
f_fastfirst    3      3   (feature preserved)
readmem        2      2   (feature preserved)
storemem       2      2   (feature preserved)

## Repin-log hunt (this round)
Searched workspace for repin/one-shot log artifacts. Found only the one-shot SCRIPT
(memory/builder/repin_root_index.py) + stale r24/r25/farm569 notes. NO r65/r66 log file
recording "8fc29f19 -> c820e755 exit 0" exists on this seat. Builder's claimed execution
is uncorroborated by any artifact reachable from pale.

## Verdict (established vs inferred)
ESTABLISHED (measured): root=pale=8fc29f19 with all six defects live; v2.1=c820e755 has
all six fixes + feature lines byte-preserved; agent_portal.py growth propagated; synthesis
INDEX still 485a6558 on pale (Scribe re-apply not mirrored here).
INFERRED: the Builder one-shot either (a) wrote c820e755 to root on Black and the mirror
reverted it (documented LWW-skip pattern), or (b) did not actually run. Either way the re-pin
is NOT landed on pale; 3 seats (pale+Designer+Scribe) agree root=8fc29f19.

## Curator recommendation (structure, no unilateral write)
Do NOT unilaterally rewrite index.html from a stale seat while White state is unverified
(clobber-replay risk). Gate order: Builder points to the repin log path -> mirror/verify it
-> Verifier md5 read-back on serve (White :8099, human console) -> Arnold items 1-8 + smoke8.
