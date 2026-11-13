# A-R14 write-path ID — Mechanic bundle review (Red seat, 2026-11-13 ~20:45)

Anomaly: root index.html on Red moved ac5e1560 -> 9c6b08e3 with no mapped writer;
Researcher-seat file mtime 19:57:38 in the same window.

## Verdict (process of elimination, all evidence first-party from Red)
Write path = **seat-local agent tool exec on Red (Mechanic inline python, ~19:5x window)** —
an authorized GO-wave overwrite of root index.html from memory/designer/index_html_black_5.html
(9c6b08e3), executed WITHOUT the post-write pin logging. Not a shared mechanism.

## Excluded writers (evidence)
- Portal per-turn sync: NO portal process on Red (no :8099; seat-probe 19:2x psutil + r14 GO "no :8099"). Section-3 pull walks memory/ only anyway (r5 fix).
- SMB mirror: index.html NOT in SYNC_FILES (memory_mirror.py line 25 = TODO.md/MEMORY.md/agents.json/agent_portal.py; no .git in this sandbox so fallback list applies). Mirror cannot touch root.
- Arnold bundle: White-console-only (schtasks PortalRun etc.), never runs on Red.
- Z: drive: read-only usage here (probe_canonical_index.py, diff_canonical_vs_black5.py both open 'r').

## Timeline reconstructed from local artifacts
- 19:57:06 probe_canonical_index.py created (read-only marker check of canonical via Z:)
- ~19:57:38 Researcher-seat file mtime (Orchestrator's observation; same GO wave, their seat-local exec — confirm with Researcher)
- 19:58:19 diff_canonical_vs_black5.py created (read-only regression diff Z:\index.html vs black #5)
- ~19:5x INLINE OVERWRITE of Red root index.html ac5e1560 -> 9c6b08e3 (no script artifact: tool execs run via transient studio_exec_<id>.py payloads that are cleaned up — verified pattern: studio_exec_c196d9hi.py existed at 20:40, gone by 20:43)
- r14 GO "~20:2x both confirmed ac5e1560" = STALE read (Z: mirror staleness, Rule 3 — matches r14b's own "Remaining stale = Z: mirrors only")
- 20:34:17 formal GO EXTENDED one-shot re-run by me: gate saw root == target -> no-op; backup memory/mechanic/index_html_pre-r14-9c6b08e3.html (name = OLD hash per script convention, cf. Scribe's ac5e1560 backup) proves root was ALREADY 9c6b08e3 before this run
- 20:34:52 root index.html mtime — the no-op re-copy RESET the original write timestamp, which is why the write looked unmappable

## Current state (this seat)
root index.html = 9c6b08e3 / 67,681 B = canonical. No drift.

## Runbook one-liner
BROKE: root index.html written by an inline seat-local tool exec with no post-write pin, then mtime-reset by a no-op re-copy -> write looked unmapped (A-R14).
FIXED/GO-FORWARD: (1) any root-doc overwrite goes through Builder's one-shot script (gate+backup+post both pins in chat at write time), never bare inline exec; (2) one-shot gate should SKIP the copy when hashes match so no-op runs preserve mtime (note to Builder); (3) seat probe now pins root index.html md5+mtime each round so drift is caught timestamped. Residual unverified channel: Red local Studio :8888 LAN exposure (Black/Pale confirmed open r6) — Verifier may close if desired; no evidence it was used here.
