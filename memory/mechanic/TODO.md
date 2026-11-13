# MECHANIC TODO — updated 2026-11-13
## Blocked at my seat (need White egress)
1. [White-seat agent] Prove write access: `echo probe > \\white\c$\Projects\Workspace\AgentPortal_V1\.mech_probe`, read back, delete. Report pass/fail + who ran it.
2. [White-seat agent] Init local git repo per memory/mechanic/MEMORY.md "Git repo handoff" (3 steps; key-safety note inside).
3. [post re-drop] Run r13 union + spot-checks on the canonical White tree — includes `memory/INDEX.md` resolvable with portal/llm/ops sub-indexes, PLUS verify the 4 meeting-round portal leaves present+indexed: upgrade-plan.md (DRAFT v2), fleet-status.md, ui-upgrades-r4.md, INDEX.md (0/4 on Red seat = expected drift; escalate before P1 deploy if missing from drop).
4. [post re-drop] Load builder-q8 alias on Black, then flip agents.json + Builder smoke same turn (key already in bundle's agents.json).

## Done this round
- r8 (auto-continue): fresh SMB probe from Red = err 5 + network-denied, data point #9; artifact hunt = no new drops (no bootstrap.bat/git/.git); bundle unchanged. Nothing executable from my seat; unblocker unchanged.
- Mini memory/todo pair created here per human directive (each-agent mini files in tandem with global).
- Red tree hash-verified vs r13 baseline: 10/10 PASS.
- Pointer-system status from Red documented (expected FAIL; canonical check is a White-side item).

## 2026-11-13 (rounds 4–6)
- Done r6: fresh SMB probe (err 5 + network-denied, data point #7); r6 artifact hunt on Red tree = none present (per-host delta); pointer audit re-run PASS (no dangling file pointers; all `->` hits are prose/quoted refs). Mini-memory updated.
- Note r6: canonical repo confirmed ON WHITE (AgentPortal_V1-git/ @ HEAD 3ee398e, MinGit in Mingit/) per Scribe — my TODO items 1–2 are satisfied on White; item 3 (canonical pointer audit = O5) still needs a seat with the White tree.
- Done: r5 re-verification from Red — SMB still error 5 (net use + net view), git absent (incl. full-tree exe scan, no zip), full memory/ pointer audit PASS (no dangling file pointers; 1 API-endpoint ref flagged as non-pointer), bundle unchanged.
- Status: items 1–4 remain open pending White egress / human on White. My seat's portion concluded r5 — close-out with Orchestrator + human unblocker.
- Done: re-verified Red seat blockage with fresh evidence (net use err5, UNC dir denied, git absent ×5 locations); pointer map 0/9 on Red tree as expected; bundle contents enumerated (2 md files only).
- Still blocked at my seat: items 1–4 above (all need White egress / human on White / post re-drop). Nothing new I can execute from Red — handing close to Orchestrator.
