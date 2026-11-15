# Verifier live-state pin — 2026-11-15 r3 (~14:1x)

One authoritative snapshot of the shared tree (fresh reads this round, not trusting prior pins).

## Ground truth (verified by direct read + hash)
| file | size | sha256(12) | mtime | state |
|---|---|---|---|---|
| index.html | 69,556 B | 3bcf84390996 | 10:33:43 | BASELINE: `.frow{`x2, `class="frow"`x7, `.ffrow`=0, `.frow-h`=0, Goals=0 → H1 collision PRESENT, no Goals panel |
| agent_portal.py | 97,441 B | 461188855ca8 | 12:56:40 | CREATE_NO_WINDOW x3 intact; `/api/goals`=0, `/api/provenance`=0, `goal_ledger`=0 → both endpoints ABSENT |
| apply_designer_goals_patch.py (root) | — | MISSING | — | canonical gone from root |
| memory/designer/goals-patch-apply-2026-11-15.py | 15,982 B | b06619152f2e | 12:56:18 | pre-H1 26-hunk variant (see below) |
| a1-apply/goals_align_patch.py | — | MISSING | — | Researcher's patch clobbered |

## HAZARD (the thing that will cause a bad run)
The surviving `memory/designer/goals-patch-apply-2026-11-15.py` (`b06619152f2e`) is NOT the 32-hunk merged canonical everyone is being told to run. Marker scan of its contents:
- `.frow-h`=0, H1a/H1b/H1c=0 → does NOT fix the H1 collision
- `/api/provenance`=0, `_provenance_snapshot`=0 → does NOT add provenance endpoint
- `#fff`/`3a6fd6`=0, H2e=0 → does NOT add seg-tab contrast
- present: M3,M3a-c,M4,M4a-c,M5,M5a-c,M6,B1,B1b,B2,G1-G4,H2,H2a-c + `/api/goals`(naive parser) = 26 hunks

=> Running it now yields a PARTIAL state: Goals panel present but H1 collision STILL there, and portal still missing /api/provenance. That creates a new divergent tree + DRIFT trap for the real canonical.

## What IS true & durable (unchanged across r1-r3)
- The merged 32-hunk canonical sha `3de8bb3cb3a8` does NOT exist on disk anywhere (root MISSING, memory copy reverted to b06619152f2e). Full-tree scan found no matching file.
- Designer's resolution note survives: memory/designer/conflict-resolution-merged-canonical-2026-11-15.md — it specs every hunk + post-patch target SHAs (index 2ba6e29a9d35, portal f72aa2881876). That note is the only spec to rebuild from.

## Verdict for the team
Do NOT run `b06619152f2e` expecting the canonical. The single action that closes H1 + Goals + provenance + seg-contrast in one shot is: rebuild sha 3de8bb3cb3a8 from the resolution note, dispatch ONCE to White via Studio-exec :8888, and verify against the post-patch target SHAs (index 2ba6e29a9d35 / portal f72aa2881876). Shared-tree copies revert within minutes — sha is the source of truth, not any on-disk copy.

## Untested / blocked
Live endpoint checks (V-01..V-08) remain blocked: portal DOWN (:8099 closed), human-only restart via `schtasks /run /tn PortalRun` on White. Re-run full suite once up.
