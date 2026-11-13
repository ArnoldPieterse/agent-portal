# Orphan-folder audit — r43 re-verification (2026-11-14, Archivist seat = Pale sandbox _default)

Trigger: Scribe r42 ("no leaf found", stray folder invisible) + Verifier r42 (stray folder absent on Black seat).

## First-party re-measurement (this round, fresh hashes)
| file | size | md5 |
|---|---|---|
| memory/archivist/orphan-folder-audit-r42.md | 3,882 B | aad1907f… |
| memory/archivist/index-pointer-batch-r42.md | 2,882 B | 8ea31427… |

Both match the r42 claims byte-for-line (mtime 05:44). The r42 round did NOT truncate on my seat — leaves landed here; the gap is cross-seat visibility only.

## Stray root archivist/ folder — still present on Archivist seat (7 files)
e982110a REPAIR / f3a31650 f1-index-patch / 4d71c6e7 fleet-md5-note / efe6cc4e goals / da18d2f6 index-integrity / 7dec653f index_check.py (v2) / 289b7ee2 provenance_audit.py (pre-fix).

## Rescue integrity re-check
- 5 unique .md copies in memory/archivist/ = byte-exact vs stray originals (md5 equal, verified this round).
- memory/archivist/provenance_audit.py d7df4e2b / 3,224 B differs from stray 289b7ee2 by exactly ONE line (unified diff confirmed): `ROOT = Path(__file__).resolve().parents[2]` — the intended canonical-location fix. Not corruption.
- Checker adjudication item stands: module INDEX points at stray-folder v2 (7dec653f); canonical copy is v1 e5862568 / 2,772 B. White-side call only; no seat overwrite attempted.

## Classification + adjudication path
Cross-seat invisibility (Scribe: leaves absent; Verifier: stray folder absent on Black) = mirror lag or mirror-scope gap for repo-root paths — consistent with the documented recurring clobber/lag pattern (MEMORY.md, TODO.md regressions this same day). NO seat re-apply performed. Adjudication belongs in Arnold's ONE White-console pass: `md5sum` of the two r42 leaves + stray-folder listing on White disk; if absent there too, mirror scope needs the repo-root path added (Orchestrator bundle item).

## Owed downstream (unchanged)
- Orchestrator: fold index-pointer-batch-r42.md lines into Arnold's bundle (root sub-index line + 6 module entries + post-adjudication checker pointer fix).
- Verifier: byte-check the two leaves once visible from Black seat.

Pin: this leaf — see TODO/round log for md5 after write.