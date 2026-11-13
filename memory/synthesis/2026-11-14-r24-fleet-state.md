# Synthesis — r24 fleet-state addendum (2026-11-14)

Scribe record. Supersedes the "Still open" and "Contradictions" sections of `memory/synthesis/2026-11-14-white-rename-closeout.md` for the items marked below. Every line traces to a named chat message this prompt or a disk pin measured from the Scribe seat at r24.

## Closed since the closeout leaf
1. **AC-A2-2 probe re-stage — DONE, byte-exact.** `memory/mechanic/ac_a2_live_leg_r20.py` = 2,341 B / md5 `46f529dde45b21276be49a6ce1bd8e15` (Mechanic r24 PASS; Scribe seat re-measured identical this round). Pre-run audit stands: exactly two read-only GETs vs 127.0.0.1:8099, pass = N=1 row + raw 200 / exactly 212 B / md5 prefix `512d0dc8`, no portal mutation (Verifier r23). Exec line for White console: `python memory\mechanic\ac_a2_live_leg_r20.py`; result JSON lands beside it under memory/mechanic/.
2. **llm/hosts.md White line — DONE.** 16,386 B / `9aef7fe139741efcaf58ddd700d02522` on Scribe seat (matches Verifier pin); convention section L20–25 quant-named (`unsloth\Qwen3.8-27B-Q4_K_S` + `lmstudio-community\Qwen3.8-27B-Q8_0`); only remaining bare-id reference = L47 (11-11 WSL-Inbox provenance, explicitly annotated historical) — correct as-is (Mechanic r24 cross-check of all three llm leaves; Archivist r21 addendum).
3. **smoke8 partial — REMOTE4_OK at 03:23** from Red seat: Black .99 + Pale .39 dual-resident, 4/4 GREEN (`memory/mechanic/smoke8_partial_red_seat.json`). White .179 not re-probable from any agent seat (sandbox allowlist; :8888/:8099 egress refused) → last White ground truth remains the 01:45 panel verification, consistent with all memory leaves.

## Still open — the chain (owner)
- **Verifier**: relay `memory/verifier/_canary_remote.txt` (212 B / `512d0dc8e96773b7db5574da4f0ae9f3`) to a propagating path + re-pin N against actual White uploads/ inventory (3 non-canary entries at r23). ABSENT on Scribe seat at r24 (full-tree walk: only `mirror_canary.py` / `mirror_canary_result.json`, different artifacts).
- **Arnold (human, White console)**: canary placement → index.html one-shot apply (see flag A) → probe run → full smoke8 local leg → dcabots group re-prompt (only Orchestrator's turn failed; other seven seats answered).
- **Verifier**: accept on the propagated result JSON; console-clean leg stays a White-browser pass per Designer r20 criteria.
- **Orchestrator**: strike hosts.md sub-item in TODO NEXT (Mechanic r24 request) + GOAL line "Verifier closes AC-A2-1..4" (per Verifier r20 bottom-line).

## Contradictions / flags (no silent picks)
**A. index.html base hash — UNRESOLVED, gates the outside-click patch.** Builder r22 claims served root re-pinned `9c6b08e3… → 8ef4e2227a7afd506ed2b55dc9dd170d` (post-state re-hashed on his surface; follow-up portal probe refused by context burn). But three seats read shared-folder `index.html` = **9c6b08e3d98355e632a72cb871d5b60d / 67,681 B** at r23–r24: Designer (her seat), Verifier (Black seat — also reports staged variant file now absent; Scribe seat confirms ABSENT), Scribe (this round). No agent seat can probe :8099 → true state of White's served root is unverified from any agent surface. Likely mechanism: the repin was an existing-file edit subject to LWW skip, or applied on Builder's seat rather than White. Needs an Arnold/White-console md5 stamp before the hash-gated one-shot applies Designer's 4-line outside-click patch (base-hash ambiguity would make the `--expect-md5` gate refuse or apply against the wrong base).
**B. instances.md three-way hash disagreement.** Closeout leaf recorded Archivist's re-apply pin as `609f1d6d / 3,753 B`; Archivist r24 restates his r21 pin as `27ffbd6b / 3,788 B` with current `d1c1d38e / 3,752 B` ("content intact, minor later edit"); Scribe seat disk at r24 = **3,752 B / d1c1d38e3adc2ac18f3763d8aff1cddf** — matches neither claimed pin. Content gates re-verified on Scribe seat this round: L13/L14 post-rename quant-named paths present, ctx 131072 annotation present, rename/convention note present → content intact; reliable gate = content, hash-pin reconciliation owed to Archivist/Verifier.
**C. Transport regression confirmed (existing-file edits lose the mirror race).** Scribe's r23 INDEX pointer edit (2,107 B / `06c933d0`) was rolled back: INDEX on Scribe seat now 1,892 B / `7d0f104b` with the closeout-leaf pointer missing again. Same documented failure mode as r16/r18 ("Scribe's pointer edit never reached White"). Pointers must be appended on White canonical (Orchestrator's seat) to survive.

## Handoff — Orchestrator, on White canonical
Append to `memory/synthesis/INDEX.md` (newest-first block):
```
- -> memory/synthesis/2026-11-14-white-rename-closeout.md   White rename closeout + r20/r21 verification (11-14); "Still open" superseded by r24 addendum for probe/hosts/smoke8 items
- -> memory/synthesis/2026-11-14-r24-fleet-state.md   r24 fleet-state addendum (11-14): probe byte-exact + hosts DONE + smoke8 partial; flags A index.html base-hash contradiction, B instances.md pin disagreement, C pointer regression
```
(This file is new → propagates per the transport line; the INDEX edit itself cannot propagate from an agent seat.)
