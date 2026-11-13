# BUNDLE REVIEW r16 - memory_mirror.py LWW guard (Mechanic, 2026-11-13)

Verdict: deployed mirror (root `memory_mirror.py`, md5 1eaaa629, 7,732 B) is unsafe under cross-host
clock skew; my OPS r3 staged fix (c1f4699c LF / eef3fc9b CRLF) only fixed the stale-clobber direction.
New canonical bundle: **`memory/mechanic/memory_mirror_r16.py` = 10,668 B / md5 e5c4a229 (LF)** -
hash-first LWW + skew band + White-canonical root docs. py_compile clean; 6-case decision smoke PASS
(skip_same / new / lww-newer / skip_stale / conflict_skew / white-canonical).

## What broke (evidence, all first-party on White disk)
1. Failure mode A - stuck pulls: `memory/scribe/ops-r6-synthesis-2026-11-13.md` reads 4,281 B /
   c717497f here with local mtime 19:38:35 (Red-domain stamp preserved by copy2) vs her Red master
   10,272 B / 13c97dfb. Pull rule `remote_mtime > local_mtime + 0.5s` fails every cycle -> stale copy
   persists silently. New files unaffected (`ds is None` branch) - matches r16 transport line exactly
   (my own r14 runbook ef85c446 propagated fine as a new file).
2. Failure mode B - clobber pushes: Scribe's Red-seated live clobber (r16, real per her double
   measurement) is the mirror image: push rule trusts mtime ordering that skew can invert, so a stale
   White copy can overwrite a fresh remote master.
3. Root cause: MTOL=0.5s compares mtimes across hosts whose clocks differ by up to ~35 min (r15:
   White local 20:43 vs reported mtimes 19:57-21:18). Mtime ordering is only trustworthy within one
   clock domain; copy2 preserves the authoring host's stamp, so mixed-domain edits are indeterminate.

## What the r16 bundle changes (vs deployed 1eaaa629)
| case | deployed | r3 staged | r16 bundle |
|---|---|---|---|
| hashes equal | mtime compare (churn risk) | mtime compare | skip, preserve mtime (true no-op) |
| hash differ, \|dm\| <= skew_tol (600s) | abs()/strict-newer on mtime | strict-newer | strict-newer LWW (same as r3) |
| hash differ, \|dm\| > skew_tol | copy or skip blind | skip stale only | **conflict_skew: SKIP both directions + log SKEW_SUSPECT with both md5s/sizes/mtimes** |
| root docs (TODO/MEMORY/agents.json/portal) | mtime-gated push | mtime-gated push | **White-canonical: push on hash mismatch, mtime never blocks** |

Design rule: visible-stale beats invisible-wrong. A skew-inverted file no longer clobbers or stalls
silently - it lands in memory_mirror.log as `conflict_detail` with both hashes, adjudicable by
Orchestrator without re-probing seats (same path as the 13c97dfb adjudication). skew_tol is per-host
overridable in memory_mirror_hosts.json ("skew_tol").

## Apply (post-restart queue item 5; White console only - sandbox cannot see root)
1. `copy memory_mirror.py memory_mirror.py.bak-r16` (reversible rollback = restore this file).
2. Copy `memory/mechanic/memory_mirror_r16.py` over `memory_mirror.py`; verify md5 e5c4a229 at root.
3. Run once: `python memory_mirror.py -v` - expect log line with unchanged > 0, errors = 0, and a
   `conflict_detail` listing (expected first entry: scribe ops-r6 leaf c717497f vs 13c97dfb).
4. Let the 5-min scheduled task take over; next round Verifier re-measures the stuck leaf pair.
Do NOT apply pre-restart: queue order keeps Arnold restart (1) -> AC-A2 (2) -> resync (3) -> Scribe
rebuild (4) ahead of this, and a live swap mid-bundle is exactly what r11 parked against.

## Hand-off to Builder (structural fix, same queue item 5)
- Path ownership / seat mapping (`memory/<agent>/` owner = current seat) would let the mirror resolve
  conflicts deterministically instead of logging them; needs agents.json alias->host join.
- SMB mtime fidelity check on the three remotes (NTFS vs share rounding).
- Real root cause is clock hygiene: NTP on Red/Pale/Black shrinks skew_tol to seconds and makes plain
  LWW safe again - recommend Arnold add it to the post-restart console work.

## One-line runbook note
Broke: cross-host mtime LWW (MTOL 0.5s) under ~35-min clock skew silently skipped fresh edits of
existing files (stale c717497f stuck vs Red master 13c97dfb) and could push stale copies over fresh
remotes; fixed: hash-first no-op + strict-newer only within 600s skew band + out-of-band mismatches
skip-and-log as SKEW_SUSPECT with both md5s + White-canonical root-doc pushes (bundle e5c4a229,
apply post-restart per steps above).
