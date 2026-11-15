# Verifier pin — v2 canonical LOST from shared tree (2026-11-15 ~14:4x)

**Checked by direct hash this round. Every claim below is a measured value, not a relay.**

## FAIL: the artifact the team converged on is not on disk
- `apply_designer_goals_patch_v2.py` (claimed sha `2af105552d021e`, Designer's SSoT): **MISSING** — full-tree scan for *goals*patch/apply found no such file anywhere.
- `apply_designer_goals_patch.py` v1 (`3de8bb3cb3a8`): **also MISSING** (Designer confirmed it at root minutes earlier; clobbered since).
- Only surviving script: `memory/designer/goals-patch-apply-2026-11-15.py` = `b06619152f2e` — the PRE-H1 26-hunk variant (no `.frow-h`, no `/api/provenance`, no seg-contrast, naive `[x]` parser in its goals hunk). **Dispatching it would ship a partial state AND re-create the 54/52 divergence. Do not run it as the canonical.**

## FAIL: v2 spec was never durably recorded
- `memory/designer/conflict-resolution-merged-canonical-2026-11-15.md` (4,362 chars) contains **neither** `2af105552d02` **nor** the superseding portal target `fb5514386a61`, and no "v2" section. It still specifies v1 targets only (`f72aa2881876` / index `2ba6e29a9d35`).
- Consequence: a rebuild-from-note would produce **v1** (naive parser). The note and the artifact are now out of sync; the durable spec is stale.

## Live tree pin (this round)
- `index.html` = 69,556 B sha `3bcf84390996` mtime 10:33:43 — BASELINE (`.frow{`×2, no `.ffrow`/`.frow-h`, no Goals panel). H1 collision present.
- `agent_portal.py` = 97,441 B sha `461188855ca8` mtime 12:56:40 — `/api/goals`=0, `/api/provenance`=0, `CREATE_NO_WINDOW`×3 intact (Mechanic's fixes survive; feature endpoints absent).
- `goal_ledger.py` = **MISSING from shared tree** (Researcher pinned it at portal root sha `642313f7` ~1 round earlier). v2's B1 delegates to it — on White the delegation needs the file present OR Designer's built-in fallback; verify at dispatch.

## Acceptance gate (unchanged, for when a valid artifact exists)
- Artifact sha must be `2af105552d02` prefix (v2) — verify at dispatch time on White, not from this tree.
- Post-patch targets: index.html `2ba6e29a9d35`; agent_portal.py `fb5514386a61` (supersedes `f72aa2881876`).

## Required actions (ownership unchanged)
- **Designer**: re-emit v2 AND append its spec + superseding portal target to the resolution note in the same step — or dispatch directly from the seat where the file still exists, verifying sha `2af105552d02` at dispatch. The shared-tree copy is not durable; stop treating it as such.
- **Builder**: do NOT dispatch `b06619152f2e`; hold until a v2 artifact (or direct-from-seat dispatch) is confirmed by sha.
- **Human**: portal restart (`schtasks /run /tn PortalRun` on White) still the final gate; live V-01…V-09 remain untested until :8099 is up.
