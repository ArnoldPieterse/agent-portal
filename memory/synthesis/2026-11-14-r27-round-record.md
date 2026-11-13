# Synthesis — r27 round record (2026-11-14, ~04:0x)

Scribe record. Every line traces to a named source in this thread or an on-disk pin measured from Scribe seat this round. Round record, no supersession.

## Landed + verified this round
1. **Verifier canary relay CLOSED** — `memory/verifier/_canary_remote.txt` = 212 B / md5 512d0dc8e96773b7db5574da4f0ae9f3 (Scribe seat mtime 03:52:43); Orchestrator, Researcher and Verifier all verified byte-exact first-party. Scribe's earlier "still absent" read is superseded. *(Orchestrator/Researcher/Verifier messages this batch; Scribe pin)*
2. **Base-hash ruling reconciled** — Verifier r26 adopts the White-canonical swap 8ef4e222 already stamped by Orchestrator; durability held, re-verified by Orchestrator this round. *(Orchestrator message)*
3. **hosts.md cross-seat skew RESOLVED by third measurement** — Archivist read 16,386 B / 9aef7fe1 (mtime 02:14) vs Mechanic 16,455 B / 2f5aafe3; Scribe seat now measures **16,455 B / 2f5aafe316fc6ac57a5203ab9de1d3d5 (mtime 03:55:08)** = Mechanic's value → Archivist's was a pre-03:55 snapshot (mirror lag), not a content contradiction. Substantive state unchanged: quant-named White folders, bare-GGUF mentions only in annotated historical lines. *(Archivist closeout; Mechanic status; Scribe pin)*
4. **instances.md confirmed at agreed pin** — Scribe seat 3,752 B / d1c1d38e (mtime 03:16:20) = r24 both-seats-agree value; the white-rename-closeout leaf's intermediate 609f1d6d / 3,753 B pin superseded (note added in that leaf). *(Archivist flag B; Scribe pin)*
5. **Researcher r27 finding: Arnold's probe leg is a deterministic FAIL as specified** — `/api/uploads` (canonical agent_portal.py L1371) walks uploads/ recursively, files only; White local uploads/ holds 5,379 pre-existing files (projects/ 5,159 + AgentPortal_V1/ 219 + DCABOTS-MOVED.md) → check[1] (exactly one row) can never pass by placement alone. Fix options: (a) amend check[1] to "canary row present, N≥1" — Researcher-recommended; (b) Arnold destructive-clean of the un-mirrored uploads/. Evidence leaf: `memory/researcher/r27-probe-n-semantics-2026-11-14.md` (4,672 B / 8d71401f on Scribe seat). Decision owed: **Verifier** (expectation ratification) + **Orchestrator/Arnold** (console-leg spec). *(Researcher message + leaf)*

## Still open (owner)
- Probe check[1] expectation amendment or uploads clean — **Verifier / Orchestrator / Arnold** (per Researcher r27).
- Arnold's White-console legs: place canary, run `python memory\mechanic\ac_a2_live_leg_r20.py`, devtools console-clean pass; result JSON `ac_a2_live_leg_r20_result.json` still ABSENT fleet-wide (Scribe seat confirmed this round) → Verifier accepts in one step when it lands with [N=1 row, raw 200 + exactly 212 B / 512d0dc8, console clean]. *(Verifier message; Scribe pin)*
- `white_load_q8_r21_dualpath.py` exec — **human leg on White console** (Builder: Black sandbox WinError 10013 + White :8888 LAN timeout re-proven from his seat; py_compile not re-verified this turn, treat as "staged clean per r21 write-up"). *(Builder message)*
- A4 apply + send-button contrast fix (FAIL #5) — **Builder**; FAIL #1 token-lock resolved (Orchestrator option b, design-tokens.md 7442c801); A4 hunks proven mechanically applicable to both candidate bases (9c6b08e3 / 8ef4e222). *(Designer r27 message)*
- One authoritative md5 stamp of White canonical index.html from the White console — **Orchestrator/Arnold** (seats split between 9c6b08e3 and 8ef4e222; Designer flag, same ask now covers hosts.md convergence). *(Designer r27 message)*
- synthesis INDEX white-rename-closeout pointer append on White canonical — **Orchestrator** (Archivist flag 1; agent-seat edits can't propagate per rollback history). *(Archivist closeout)*
- dcabots re-prompt + E14 + smoke8 + farm.py:569 — unchanged owners per prior record.

## Contradictions / evidence flags (no silent picks)
- hosts.md 16,386/9aef7fe1 vs 16,455/2f5aafe3 — resolved this round by Scribe third measurement (Landed #3); no content contradiction.
- Designer's `memory/designer/a4-dual-base-verify-r27.md` not yet present on Scribe seat at sweep time (mirror lag or post-sweep write) — pin to confirm next round; message claims 4,788 B / 217d63aa.

## Lane status
All seven agents [CONCLUDED] this batch. Scribe corrections landed in `2026-11-14-white-rename-closeout.md` (item-1 correction + item-6 supersede note, both flagged by Archivist). Nothing further owed from Scribe until the result JSON or a base stamp lands.

## Scribe-seat pins this round (first-party)
- hosts.md 16,455 B / 2f5aafe316fc6ac57a5203ab9de1d3d5 (mtime 03:55:08)
- instances.md 3,752 B / d1c1d38e3adc2ac18f3763d8aff1cddf (mtime 03:16:20)
- memory/verifier/_canary_remote.txt 212 B / 512d0dc8e96773b7db5574da4f0ae9f3 (mtime 03:52:43)
- memory/mechanic/ac_a2_live_leg_r20_result.json ABSENT
- memory/researcher/r27-probe-n-semantics-2026-11-14.md 4,672 B / 8d71401f61275ef0018f165f6cf1c17f (mtime 04:00:35)
- memory/designer/a4-dual-base-verify-r27.md ABSENT on Scribe seat at sweep time
