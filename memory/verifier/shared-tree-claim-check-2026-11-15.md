# Verifier — shared-tree claim check (2026-11-15, auto-continue 3/3)

Re-pinned the live shared tree from Black host sandbox (`C:\Users\black\.unsloth\studio\sandbox\_default`) and checked the three fixes claimed done this round against the actual bytes. **All three are NOT present in the shared tree.**

## Final pin (this round)
- `index.html` sha256 = `2ba6e29a9d35fb3f0eecdc8e10c49df16c6a7715d670f91f18e2e72fabf3c355`
- `agent_portal.py` sha256 = `25fd9457b2cb8771e39e52dc5eda270bd896aed64cfd68384ecf5cb419e76120`

## Finding 1 — H1 naming collision STILL LIVE in index.html (Builder + Designer claims not landed)
- Live file at sha `2ba6e29a9d35` (the "acceptance target"): 6 dialog rows still `class="frow"` (L266/275/279/283/289/293); fleet row `class="frow-h"` (L680); CSS `.frow` L92 + `.frow-h` L120-121.
- **Zero `.drow`** anywhere. Builder's claimed rename of 6 dialog rows `.frow`→`.drow` is NOT in the shared tree.
- Designer reported "re-ran patch: 0 applied / 31 skipped, byte-identical no-op, all 15 post-checks PASS" — but this sha still contains the collision, so H1 is not durably resolved here.

## Finding 2 — dead code in /api/provenance STILL PRESENT (Orchestrator + Mechanic claims not landed)
- `agent_portal.py` L1685 route; try/except L1687-1691 always returns (L1689 success, L1691 except).
- L1692 `# Goal Velocity dashboard (2026-11-15, Designer)...` + L1693 `return self._json(200, _goals_snapshot())` are **unreachable dead code** — still present.
- Both Orchestrator and Mechanic independently claimed to have removed these same lines. Neither removal is in the shared tree (sha unchanged from my prior pin: `25fd9457b2cb`).
- Marker counts: `_goals_snapshot()` x3, `/api/provenance` ref x1, `/api/goals` ref x1.

## Finding 3 — Mechanic's sha claim is false for this host
- Mechanic reported `agent_portal.py` now sha `29ca92639845`. Live on Black = `25fd9457b2cb`. Their edit did not reach the shared tree I read.

## Root cause (confirmed)
Per-agent sandbox edits are being **clobbered by the SMB mirror** before/at sync: local "verified on disk" != "landed in shared tree." This is the recurring mirror-clobber / tree-cycling defect, and it has now swallowed three separate claimed fixes (Builder H1, Orchestrator dead-code, Mechanic dead-code). Durable fixes must be applied on a host whose write survives the mirror cycle.

## IP-scrub gate — one defensible number
Scan: all text files, no extension filter, skip `.git`/`git-smoke`/`_dcabots_test_src`.
- **125 files / 240 occurrences** of `192.168.x.x`.
- By dir: memory=66, root=45, unsloth-tmp=9, MinGit-x=4, designer=1.
- By ext (file count): .md=51, .html=34, .py=14, .bak*=12 (transient backups), .txt=6, .json=5, .cnf=2, .dist=2.
- Why prior counts differ: Mechanic 96 = .md/.py/.json/.txt only (excluded the 34 .html + .bak); Archivist 85 / Verifier-prior 86 = memory+top subset; Orchestrator ~50 = likely git-tracked-only. The `.html` files are the main undercount driver.
- `memory/llm/hosts.md` still holds 13 occurrences.

## GAP flagged (needs a git-bearing host)
- **No `.gitignore` at this tree's root** (`os.path.isfile(.gitignore)` = False). The "hosts.md is UNTRACKED via .gitignore" story depends on an ignore rule not present in the shared tree I can read. A git host must confirm hosts.md is actually untracked, else auto-sync can re-publish it.

## Disposition
- Not agent-unilaterally fixable durably from this box (mirror clobber). Handoff: Builder/Designer/Mechanic re-apply on a mirror-surviving host; Orchestrator/gittier host confirms hosts.md tracking + .gitignore.
- IP scrub remains a HUMAN decision gate.
