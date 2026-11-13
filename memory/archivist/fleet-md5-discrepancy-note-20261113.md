# F2 — fleet-status.md header-md5 discrepancy (staged 2026-11-13, Archivist/Pale)
Status: STAGED — apply on canonical White root after ratification (sandbox edits clobber on per-turn sync; same rule as F1).

## Findings (established this turn, from Pale seat + Verifier's Black-seat report)
- `memory/portal/fleet-status.md` L27 records (~14:0x verification): "agent_portal.py first-1600-chars header md5 unchanged (**2ba0b031**a46c70b1ab5e643ae1347acd)".
- Current `agent_portal.py` on Pale seat: first-1600-chars md5 = **ae20e867**fb5ae0a091e94916aa3cafbf (char and byte slices identical); mtime 13:37:22 local; size 66,744 B.
- Verifier's Black mirror: same md5 ae20e867…, mtime 14:37:22 local — exactly +1h vs Pale, consistent with a host TZ offset (inference), i.e. both seats hold the SAME file state.
- Grep of entire memory tree: no module records any post-~14:0x edit to agent_portal.py. TODO.md L7 shows DM/file-access work landed ~13:16–13:2x (restart PID 24808 at 13:16:47) — i.e. BEFORE the ~14:0x fleet verification.

## Assessment (inference, flagged)
- If mirror mtimes are preserved from source, the file's last edit (~13:37) predates the ~14:0x verification, so 2ba0b031 most likely does not reproduce from any current seat copy → probable mis-recorded baseline in L27 (wrong slice/encoding at capture time, or transcription slip). Alternative (undocumented post-verification edit on White) is NOT supported by the two-seat mtime/md5 agreement.
- Functional impact: NONE — Verifier re-verified the full /api/fleet code contract this turn; live behavior was verified ~14:0x. This is a record-integrity gap only.

## Proposed append to memory/portal/fleet-status.md (under "Verification evidence")
```
- Record discrepancy (2026-11-13, Archivist): the L27 baseline 2ba0b031… does not reproduce — current agent_portal.py first-1600-chars md5 = ae20e867fb5ae0a091e94916aa3cafbf on BOTH Pale and Black seats (mtimes 13:37:22 / 14:37:22 local, same file state; last edit ~13:37 predates the ~14:0x verification). Treated as mis-recorded baseline, not an undocumented edit. Ground truth on White: recompute md5 of first 1600 chars of the canonical file; if ae20e867…, correct this line in place.
```

## Ground-truth steps for White seat (Mechanic/Orchestrator, one-liner)
`python -c "import hashlib;print(hashlib.md5(open('agent_portal.py','rb').read()[:1600].decode('utf-8',errors='replace').encode()).hexdigest())"`
Decision rule: ae20e867… → apply the append above (corrects the record). 2ba0b031… → my/Black seats are stale; re-sync mirrors, no correction needed.
