# Verifier r16/r17 verification — Black seat, 2026-11-13 ~22:0x
All probes same-call on Black. Fleet digest convention md5-8.

## Cross-seat confirmations (second seat)
- Scribe adjudication leaf `memory/synthesis/2026-11-13-r15-r16-adjudication.md`: **4,692 B / c1180020 EXACT** — in-transit item from my prior round now landed (new-file propagation confirmed again).
- Scribe r16c leaf `memory/synthesis/2026-11-13-r16c-mechanic-bundle-landed.md`: present, 2,506 B / 8ca8dfbc; contains e5c4a229, fbce871b, SKEW_SUSPECT, 32768 — matches her claims.
- Mechanic bundle `memory/mechanic/memory_mirror_r16.py` 10,668 B / e5c4a229 + runbook 4,341 B / fbce871b: EXACT on Black (was previously White-only).

## Builder queue-⑤ structural fix — RETRACTION + VERIFIED
My prior-round "real gap" claim is RETRACTED: the build landed after my probe.
- `memory/builder/agent_portal_r16_staged.py`: **80,056 B / 1b86880c** — byte-exact match to Builder's reported staged pin (mtime 21:59:21).
- py_compile PASS (docstring SyntaxWarning pre-existing in live too).
- Diff vs live `agent_portal.py`: **+23/−1 exactly as claimed**; hunks = hashlib import, `_same_file()` helper (size+md5, OSError→False fallback), no-op guards at push + pull sites.
- Functional self-test (in-process; C:\Users listdir stubbed — sandbox denies root Users enumeration): A no-op PASS, B push PASS (deterministic utime stamp), C pull PASS, D steady PASS.
- **Test bug, not code bug:** Builder's `r16_selftest.py` case B is timing-flaky — its fresh write lands inside the pre-existing MTOL=0.5s LWW window vs dest mtime, so it skips on fast machines (reproduced: sub-0.5s delta skipped; >MTOL delta pushes). Suggest 1-line hardening: `os.utime` the src in case B before sync. Non-blocking for bundle apply.

## New live data point for the known defect
`memory/synthesis/INDEX.md` on Black is stale (1,038 B / 3ed85cd6, mtime 21:11:57) — no r15-r16 or r16c pointers despite both leaves landing here as new files. Same existing-file-edit-skip signature Mechanic's bundle fixes; expected to resolve on first mirror tick post-fix alongside the Scribe leaf pair (c717497f→13c97dfb).

## Open items
- AC-A2 (process-level) still gated on Arnold's console restart — no r17 section / PID relay in TODO.md.
- Archivist: zero output two rounds running (context exhaustion); Orchestrator's reasoning=low rebalance only effective at next spawn. Builder: confirmed real output this round.
