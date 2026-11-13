# MTIME-GUARD PATCH — 5-min SMB mirror (Mechanic, 2026-11-13 ~19:1x)

Assigned by Orchestrator OPS r3: "add mtime guard to the 5-min SMB mirror (overwrite only if
source mtime > dest)". Clobber vector found + fixed; UNC A/B verdict included below.

## What broke / what fixes it (one line)
Broke: `push_tree()` in memory_mirror.py used `abs(src_mtime - dst_mtime) > MTOL` -> a STALE source
overwrote a NEWER dest (last-writer-wins with abs() = stale copies can win; same family as the
Scribe-compression clobber confirmed at source ~20:0x). Fix: strict-newer rule everywhere - copy ONLY
when `src_mtime > dst_mtime + MTOL` (or dest missing); same-age/newer dests are never overwritten and
are counted per run (`skipped_stale`) in the audit log so clobber-avoidance is visible.

## Anchors (hash-verify before/after)
- base file (on White): memory_mirror.py  md5 `1eaaa6299dab9850751fc32782218ba7`  7732 B  (r29 version w/ pull-back)
- fixed file:           memory/mechanic/memory_mirror_fixed.py  md5 `c1f4699cb0277368a5a68694f30c5184`  186 lines, py_compile OK

## Apply (White-local, Arnold)
1. Confirm base: `certutil -hashfile memory_mirror.py MD5` == 1eaaa629... (if different, STOP and re-diff against the hunks below).
2. Replace memory_mirror.py with memory/mechanic/memory_mirror_fixed.py (drop-in; same CLI, same log format + one new key).
3. No restart needed - the \\MemoryMirrorRun schtasks job runs the script fresh each 5-min cycle.
4. Verify: `python memory_mirror.py -v` -> expect per-host results incl. `"skipped_stale": N`; next scheduled log line in memory_mirror.log carries the same key.
5. Propagation: if memory_mirror.py is in the git allowlist (~43 files), the fix reaches all remote seats on the next mirror cycle automatically; if not, add it to .gitignore allowlist so future drift is visible.

## Hunks (7, all asserted 1-of-1 against the base md5 above)
1. module docstring: design note rewritten to document the STRICT-NEWER rule (prevents regression to abs()).
2. push_tree signature/docstring: returns `(pushed, errors, skipped_stale)` instead of `(pushed, errors)`.
3. push_tree copy decision: `abs(...) > MTOL` -> three-way: dest missing / src strictly newer -> copy; else append rel to `skipped`.
4. allowlist push loop: init `skipped_allow` (copy rule unchanged - already strict-newer).
5. allowlist push loop: add `else: skipped_allow.append(rel)` audit branch.
6. call site: `p2, e2, sk2 = push_tree(...)`.
7. result dict: adds `"skipped_stale": len(sk2)+len(skipped_allow)` (+ `skipped_stale_files` sample when non-zero).

Pull-back loop (remote memory/ -> White) was already strict-newer (`ss.st_mtime > ds.st_mtime + MTOL`) - UNCHANGED.
Known limitation (unchanged, by design): TODO.md/MEMORY.md are push-only; only memory/ pulls back, so the
canonical source can still be clobbered by the White-local per-turn sync (_sync_workspace_to_sandbox in
agent_portal.py) - that defect is OUT OF SCOPE of this patch and belongs to Arnold's one-shot list.

## UNC routes A/B - verdict (probes: probe_unc_ab.py -> probe_unc_ab_result.json 19:08; probe_unc_ab2.py -> probe_unc_ab2_result.txt 19:09, both from Red seat)
- Route A = TTL / reconnect-on-fail (current ensure_conn). Route B = keep-alive / sleep-tolerance.
- Data: net use to C$ from RED fails on all 3 hosts (Red self: error 5 in 0.02s; Pale + Black: error 5 after ~21.06-21.07s). Port follow-up at 19:09: ALL three :445 OPEN, Pale+Black :8888 HTTP 200 (awake), White :8888 timeout = known firewall baseline since r7-r16.
- Reading: the 21s Pale/Black failures are SMB session-level rejections of Red's creds (port open, host awake) - NOT sleep, NOT a dropped port. New durable fact: admin-share mapping works from WHITE only (mirror runs fine all day; canary 18:09 ok lag 336s); Red-seat C$ maps to Pale/Black = denied (egress-block series data point #11).
- VERDICT: Route A is sufficient for the 5-min cadence. Sessions on White have established + used cleanly all day; when a host IS asleep, ensure_conn already recovers via delete+re-auth at bounded cost (~20s per sleeping host, logged). Route B (keep-alive) adds nothing at a 5-min interval and cannot survive host sleep anyway. NO NEW MACHINERY.
- Optional closer (White-local, low priority): create session -> idle 120s -> re-touch, to put direct evidence on file that session TTL >> 5min while hosts are awake.

## Files
- memory/mechanic/memory_mirror_fixed.py   drop-in replacement (this bundle's anchor)
- probe_unc_ab.py / probe_unc_ab_result.json      A/B session probe (read-only; cleans up its own net use)
- probe_unc_ab2.py / probe_unc_ab2_result.txt     port follow-up (sleep-vs-firewall discriminator)
