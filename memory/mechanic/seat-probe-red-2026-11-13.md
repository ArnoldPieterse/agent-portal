# Mechanic seat probe — Red Red (2026-11-13 ~21:3x)

For Verifier AC-A2 + Orchestrator evidence file. All facts read from this seat just now.

## Hashes on THIS seat (Red sandbox _default) — PRE-FIX
- agent_portal.py md5 58f8d7f8 (mtime 18:36) — SYNC_LWW still ["TODO.md","MEMORY.md"], section-3 LWW pull present (line ~160)
- memory_mirror.py md5 1eaaa629 (mtime 18:41) — push_tree uses abs(src-dst)>MTOL, no skipped_stale
=> These match the plan's "from" hashes. b2a299ef/c1f4699c NOT present on Red.

## Portal process on Red
- psutil: NO portal/8099 process on Red (only sandbox execs). Running PID 1240 is on White — consistent with plan. No local clobber source from this host.

## Canonical reachability from Red — BLOCKED
- UNC \\\\White\\C$ -> WinError 65 (network access denied; auth refused, NOT timeout => White is up on SMB, 17:18 regression did not recur)
- No creds for White in local memory_mirror_hosts.json (it's a synced copy of the SOURCE-side config: targets = Red/Pale/Black only)
- No .git in this sandbox; git.exe lives at canonical HERE/mingit — no fetch path
- memory_mirror.log is canonical-only (not in sync allowlist) — no local copy
=> I CANNOT relay canonical md5sums from this seat. Needs Arnold/White one-shot: `cd <canonical HERE> && certutil -hashfile agent_portal.py MD5 && certutil -hashfile memory_mirror.py MD5` + `type memory_mirror.log | find /n ""` tail + scheduled-task status for the 5-min mirror.

## Why pushes stopped landing (evidence)
- Last sync arrivals into THIS sandbox: MEMORY.md 19:19, TODO.md 19:14, scribe file 19:13 => push stream to Red stopped ~19:2x (Verifier's seat: ~20:13 — same stall pattern)
- White SMB reachable (auth refusal, not timeout) => not the 17:18 network regression
- Mirror runs fixed c1f4699c FROM DISK (independent of portal PID 1240), so if the 5-min task were alive, pushes would continue regardless of the pending restart. Stalled stream therefore points at White-side scheduler/task state or per-turn sync inside PID 1240 — both verifiable only by a White one-shot.

## Runbook note (one-liner)
- OPS r5 landed canonical-only; Red/Pale seats hold pre-fix copies (push-only rule) with no local portal process => clobber risk dormant until merge. If seat push streams stall while White SMB answers auth-refusal, suspect the 5-min mirror scheduled task on White before suspecting the network.
