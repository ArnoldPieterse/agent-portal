# Researcher analysis — OPS r3 sync clobber (2026-11-13)
For Mechanic (mtime guard + UNC A/B) and Orchestrator (escalation evidence). Seat: White sandbox; all code findings verified by reading local files this round.

## 1. The mtime guard ALREADY exists — the clobber must bypass it via content-stale/fresh-mtime
`memory_mirror.py` (runs on White, pushes to Red/Pale/Black `\\ip\\C$\\Users\\<user>\.unsloth\studio\sandbox\_default`, pulls back remote `memory/`):
- Root allowlist push (line ~120): `if ds is None or ss.st_mtime > ds.st_mtime + MTOL` — direction-correct.
- **`push_tree()` for the memory/ tree (line ~89): `abs(ss.st_mtime - ds.st_mtime) > MTOL`** — asymmetric bug: if the LOCAL file is OLDER than the remote copy by >0.5s it still re-copies local→remote, overwriting newer remote content.
- r29 pull-back (line ~145): `ss.st_mtime > ds.st_mtime + MTOL` (remote newer only) — direction-correct, but **memory/** only; it cannot touch root files like MEMORY.md/TODO.md/index.html.
- All copies use `shutil.copy2` (preserves mtime), MTOL=0.5s.

**Structural weakness:** every guard compares timestamps, never content. Any in-place rewrite on any host — portal `/api/memory` write, an agent's `edit_file`, a git checkout/reset, or even opening+resaving — resets that copy's mtime to "now" while its CONTENT is stale. A fresh-mtime stale file passes every guard and wins last-writer-wins. This matches both observed events (Scribe compression section lost; goal line rolled back to 14:0x text) without requiring mirror lag.
**Recommendation:** sha256 compare in the guard (copy only on hash mismatch); on genuine conflict (hashes differ, both mtimes fresh) do NOT silently last-writer-wins — quarantine (`<name>.stale-<host>-<ts>`) + log line. Also flip push_tree's `abs()` to direction-correct. The r13 union spec's "newest mtime wins" has the same blind spot.

## 2. TTL-vs-sleep: SMB client cache cannot explain multi-minute staleness (MS Learn, authoritative)
Windows SMB client defaults (HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters):
| setting | default |
|---|---|
| FileInfoCacheLifetime (file metadata) | 10 s |
| DirectoryCacheLifetime (directory metadata, absent leases) | 10 s |
| FileNotFoundCacheLifetime | 5 s |
| CacheFileTimeout (cached file data after last handle closes) | 10 s |

Source: https://learn.microsoft.com/en-us/windows-server/administration/performance-tuning/role/file-server/ (last updated 2025-02-24)

**Consequence for the A/B test:** on a live connection, any client-side stale read is bounded to ~10 s. Our mirror runs every 300 s — so staleness observed across cycles is NOT SMB cache TTL. Remaining candidates: (a) host sleep/hibernate window straddling a run (server unreachable → `ensure_conn` should log an error; half-open TCP after wake is the exotic case — [MS-SMB2] connection-loss handling re-validates durable handles on reconnect, server stays source of truth); (b) fresh-mtime stale content per §1. Suggested route design: A = `\\ip\\C$` direct admin share vs B = mapped drive / named share, BUT add **route C = "who else writes the destination"** — see §3; without it, A/B may test the wrong variable.

## 3. Root MEMORY.md clobber is NOT explainable by this mirror script (negative result)
The r29 pull-back only pulls `memory/**` into local; root allowlist push is White→remotes with direction guard. So for a STALE goal line to appear at the White-canonical root MEMORY.md, one of:
1. A remote host runs its own mirror WITH White as a destination and pushed a fresh-mtime stale MEMORY.md (line ~120 guard passes if the remote copy's mtime is newer). Not verifiable from this seat — no visibility into remote host configs.
2. A White-local write: git ops (milestone commit/reset; `.git` unverified from any seat — one-shot #1), portal `/api/memory`, or an agent edit that was later reverted.
**Note:** my sandbox has NO `.git` (checked) and index.html here is 64,100 bytes, sha256 `76e77aa4cdf57400…`, containing neither `filesPanel` nor A3-B anchors — confirms "White copy has neither edit" from my seat for Verifier's line-exact check.

## Confidence
- Verified high: §1 code facts, §2 MS Learn table, §3 no-.git / index.html hash (all read locally this round).
- Inference medium: clobber path = fresh-mtime stale write + some copy step; exact writer unknown pending Arnold one-shots #1/#3 and whether remotes mirror-back to White.

## CLOSURE 2026-11-13 ~21:1x (OPS r5) — root cause confirmed, writer path closed
Orchestrator's r5 verdict matches my mechanism finding, now code-verified from this seat against canonical disk:
- Root cause = per-turn sync section-3 LWW PULL of TODO.md/MEMORY.md in agent_portal.py: a stale whole-file rewrite from any seat gets a fresh mtime and wins the 0.5s-tolerance timestamp compare. This is exactly my r3 mechanism ("fresh-mtime stale write + copy step"); the SMB mirror is EXONERATED as writer (pulls memory/ only) and _auto_commit has no restore path (r4 audit).
- Fix verified on disk this round (Researcher goal #6 spot-check, all values re-computed locally):
  * agent_portal.py md5 b2a299ef5bb3e058b0dfcf4f57542d5d (claim b2a299ef OK); pull loop now has explicit skip: `for rel in SYNC_LWW: if rel in ("TODO.md","MEMORY.md"): continue` — memory/ pull intact; py_compile OK.
  * memory_mirror.py md5 c1f4699cb0277368a5a68694f30c5184 (claim c1f4699c OK); skipped_stale audit line x4; strict-> guard present; py_compile OK.
  * Mechanic staging cross-check: memory/mechanic/memory_mirror_fixed.py md5 eef3fc9bf9b2c2fc5bf44d37b0801d8f (CRLF transfer copy); its LF-normalized hash == c1f4699c == canonical => staging IS the applied fix, chain intact.
  * index.html canonical md5 ac5e15600b9ca4d56ef028ac800b0adb; opsBtn x3, actPanel x6, filesBtn/filesPanel x0 — matches r5 ground-truth line exactly (Files panel NOT in canonical).
- Status: clobber path CLOSED for root docs PENDING portal restart (Arnold one-shot #1) to load the exclusion into PID 1240; residual risk (mirror PULL side of memory/ still timestamp-only) remains open per r5 log — a fresh-mtime stale remote memory LEAF could still win a memory/ file. sha256-compare + quarantine is the next hardening step if any further clobber appears.
- Confidence: HIGH (all four hash/guard facts re-derived from local disk this round, not copied from chat).

## UPDATE r6 (11-13, Researcher seat probe)
Seat-divergence matrix for the "fixes lost" reports:
- White sandbox (_default, my tool root): agent_portal.py md5=b2a299ef, memory_mirror.py md5=c1f4699c, mtimes 19:13 — FIXED hashes intact. TODO.md carries r5 text (3 hits); MEMORY.md goal line stale (0 r5 hits, mtime 19:21) = 4th rollback observed locally.
- Red (Mechanic), Pale (Designer), Verifier seat: pre-fix copies (58f8d7f8 / 1eaaa629). Builder re-applied on its own seat -> second functional variant (new md5s, 8/8 behavioral pass) — drift only; canonical->seat push supersedes it when sync resumes.
Conclusion: no evidence canonical was reverted. The ACTIVE clobber source is the LIVE portal process (PID 1240, started pre-fix), which still executes old two-way LWW root-doc sync in memory despite fixed files on disk — explains post-r5 MEMORY.md rollback #4. Portal restart (Arnold) remains the only action that closes the path; until then treat any seat's pre-fix copy as inert (no portal runs from it: Red confirmed none).
Open for Arnold (definitive): md5 of the two files at White's WORKSPACE root (not sandbox) + restart.

## UPDATE r7 (2026-11-13 ~21:4x) - Scribe contradiction RESOLVED: different seats, no clobber on mine
- Re-probe of my seat (CWD C:\Users\<white>\.unsloth\studio\sandbox\_default): agent_portal.py STILL b2a299ef @ 19:13:47, memory_mirror.py STILL c1f4699c @ 19:13:48 - original r5 fix intact since my last verification. push-only=True in portal, skipped_stale=4 in mirror.
- Builder's 563cd9b3/2774436c (mtime 20:17) is NOT in this folder despite Builder self-identifying as "White sandbox shared folder" => Builder operated on a DIFFERENT root than mine. Scribe's first hypothesis ("they read different seats") confirmed; no live clobber of agent_portal.py needed to explain the record.
- Seat-divergence final matrix: White-sandbox (mine) = original fix b2a299ef/c1f4699c; Builder/Verifier seats = re-authored 563cd9b3/2774436c (AC-A2 PASS on function); Red/Pale/Scribe seats = pre-fix 58f8d7f8/1eaaa629 (dormant, push-only, no local portal procs).
- My seat's root docs are STALE: TODO.md a2b0a0b2 @ 19:27, MEMORY.md 4921286a @ 19:27 (predate Orchestrator's landed 2e905f33/87d14edf) - push stream to this seat also dead ~19:2x, same as Red. No seat's view is "live canonical".
- Workspace root (PID 1240 launch dir) unreachable from my tools: parent C:\Users\<white>\.unsloth\studio => WinError 5; walk finds no other agent_portal.py. Canonical-root md5 + restart remain Arnold-only (White-local), plus one-shot #5 (Black index.html) and hunk landing.
- Confidence: HIGH on seat-state matrix (all four data points read live from disk this round); the only unverifiable fact left is which copy PID 1240 actually loaded - behaviorally irrelevant to AC-A2 (both variants function-verified), operationally relevant only for the restart.

## UPDATE r8 (2026-11-13 ~22:3x) - rollback #6 observed live; single gate still Arnold-only, plus one newly found gap
- MEMORY.md goal line rolled back AGAIN on my seat: md5 10858d7b, text = old "FLEET PANEL BUILT..." 14:0x line (NEXT: announce ops processes + goals). This is rollback #6 per the OPS r6 numbering. Expected behavior while PID 1240 still runs pre-fix two-way LWW in memory - NOT a new failure mode; disk-side fix remains intact (agent_portal.py b2a299ef, memory_mirror.py c1f4699c, both re-read live this round). Reinforces: no root-doc re-sync is useful until the portal restart; every such sync just adds evidence for Arnold.
- GAP FOUND: `designer/files-panel-hunks-r5.md` (named in the OPS r6 single gate as the file to "apply at canonical") does NOT exist anywhere in this seat's tree - recursive dir search for *files-panel* = 0 hits; memory/designer/ contains only MEMORY.md + TODO.md. Per r4/r5 relay rules, Designer's re-land lives in her Black-seat sandbox and root files never mirror (memory/ leaves only). => The gate as written is BLOCKED from my seat: nothing exists for Arnold to apply until Designer posts/DMs the hunks verbatim. Confidence HIGH (exhaustive local search).
- Non-blocking deltas: index.html still ac5e1560 at this seat (one-shot #5 Black fetch not yet executed); Builder's claimed repo-root file builder-ops-r5-retest-2026-11-13.txt absent here - consistent with it being a Black-seat artifact (function already verified by Verifier, no action needed).
- Bottom line for Orchestrator: the single gate splits into two prerequisites - (a) Designer delivers hunks verbatim to chat/DM (owner: Designer), then (b) Arnold's White-local bundle: restart PID 1240 + one-shot #5 fetch + apply hunks. Verifier AC close remains after (b).

## UPDATE r16 (2026-11-13 ~22:5x) - A-R14 closed on White; the propagation gap is Red->White specific
- First-hand re-probe (White): root index.html = 9c6b08e3 / 67,681 B, mtime 19:57:38 unchanged since the r14 GO wave - zero drift.
- A-R14 note LANDED on White: memory/archivist/seat-root-anomaly-r14.md = 1,560 B / md5 0fdf4de3 (mtime 20:38:45) - full record incl. Archivist's appended Researcher-mtime detail ("not independently probed" attribution intact). r14c open item #1 is closable on bytes.
- A-R14 write path corroborated from White: memory/scribe/index_html_pre-r14-ac5e1560…adb.html = 64,100 B / md5 ac5e1560 present on White (r14b byte-confirmed) => White root WAS pre-GO stale; the observed 19:57:38 mtime IS Scribe's r14 GO one-shot overwrite. Combined with Mechanic's Red-side mapping (his inline exec ~19:5x, probes bracketing 19:57:06-19:58:19), BOTH anomalous root writes are seat-local tool execs during the r14 GO wave - no hidden shared mechanism. Confidence HIGH (backup bytes + mtimes first-hand). Note's "Hypothesis (UNVERIFIED): workspace->sandbox sync" is superseded by this; its open items can be struck once Mechanic's leaf propagates.
- Propagation lane finding: Pale->White WORKS this round (Archivist note with fresh in-round append arrived at 20:38:45); Red->White GAP - Scribe's rewritten leaf memory/scribe/ops-r6-synthesis-2026-11-13.md still 4,281 B / c717497f / FINAL STATE x0 on White (mtime 19:38:35; her claimed 8,626 B / d3bd22be not landed), and memory/mechanic/a-r14-write-path-2026-11-13.md absent. If file B is still stale after one more mirror cycle => per Scribe's pre-registered rule = Red-lane transport/LWW failure, owner Mechanic bundle review; worst case her rewrite was itself clobbered back on Red by two-way LWW (unverifiable from White).
- Canonical-leaf ambiguity FLAGGED: both memory/synthesis/2026-11-12-consolidated-state.md (5,477 B / 06611885, r14 FINAL STATE x1, Orchestrator-appended, intact on White) and Scribe's file B (Red superset incl. clobber addendum) now carry the section - team needs one canonical + SUPERSEDED mark once B lands.

## UPDATE r17 (2026-11-13 20:4x local) — White-root adjudication of Verifier's LWW-clobber escalation
First-hand re-probe, local clock 20:47:27:
- TODO.md = 78,630 B / md5 8852f966 (mtime 20:45:04): r15 section on top (x6), r14c x4 intact -> Verifier's claimed regression (r14b top, 'r14c' x0 @21:37:51) NOT present on this root.
- synthesis/2026-11-12-consolidated-state.md = 5,477 B / md5 06611885 (mtime 20:40:15), 'r14 FINAL STATE' x1 -> Verifier's claimed clobber (4,077 B / e1083a5c @23:37:40) NOT present on this root.
- Clock fact: both of her cited mtimes postdate my current local time -> impossible on this host's timeline; read as different-root observation or cross-host clock skew (skew already flagged in r15).
- New landing here: memory/mechanic/a-r14-write-path-2026-11-13.md = 3,080 B / md5 ef85c446 (mtime 20:42:07 source-preserved) -> r15's 'mechanic note missing' line is stale for this root; propagation is file-specific, not wholesale-blocked.
- Still stale here: scribe leaf 4,281 B / c717497f vs her verified Red rewrite 10,272 B / 13c97dfb -> transport-failure condition holds for that file only.
- index.html unchanged 9c6b08e3 / 67,681 B (7th+ stable round).
Verdict: the two 'live clobber' measurements are a single-seat observation, unconfirmed on my root; her evidence leaf (54082935 / 2,158 B) and this addendum are both on disk as paired input for Mechanic's post-restart bundle review.

## UPDATE r17b (auto-continue re-probe, local ~20:5x) — r16 pins re-verified; one new landing
Re-ran full pin set on White root after Orchestrator's r16 write landed:
- All five r16 md5 pins EXACT: synthesis leaf 5,477 B / 06611885 (FINAL STATE x1), mechanic runbook 3,080 B / ef85c446, scribe leaf 4,281 B / c717497f (still stale vs Red 10,272 B / 13c97dfb — third consecutive no-move round; existing-file LWW-skip persists), verifier evidence 2,158 B / 54082935, ps1 2,429 B / 2490793a. TODO.md = 81,433 B / f4505513 (mtime 20:48:33): r16 section complete on disk, +2,803 B over the 78,630 B pre-write baseline — sequential write, not a clobber.
- NEW LANDING post-r16: memory/builder/repin_root_index.py = 3,267 B / md5 717368ae (mtime 20:45:32) — r16 said 'not yet propagated to White' and pinned Builder's seat copy at 2,683 B / 14479d0f. Bytes differ by +584 B from his seat pin => revision mismatch or partial write; per r16's own gate the one-shot must NOT run on White until md5 is reconciled with Builder's current seat copy. Flag to Orchestrator/Builder (DM). No bare inline root writes in the interim — rule stands.
- index.html re-pinned: 9c6b08e3 / 67,681 B, mtime unchanged (8th consecutive stable round).
- Post-restart queue items are all owned by others (Arnold human leg first); no open lane remains for Researcher. My r17 adjudication input stands as-is.

