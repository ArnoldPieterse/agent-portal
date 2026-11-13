# AC-A2 R24 DISK RECONCILE — Researcher seat, 2026-11-14 (shared agent folder view)

Supersedes `ac-a2-live-leg-status-final-2026-11-14.md` (03:32) for everything below; that leaf's "WCAG-AA intact at 8ef4e222" claim referred to the staged variant, not the current root state — corrected here.

## Verified on disk this sweep (hashes re-derived, not relayed)
| item | size | md5 | status |
|---|---|---|---|
| index.html (root) | 67,681 B | 9c6b08e3d98355e632a72cb871d5b60d | PRE-SWAP bytes — content check: `.aev .at{color:#6b7688` present; WCAG fix NOT in canonical |
| memory/mechanic/ac_a2_live_leg_r20.py | 2,341 B | 46f529dde45b21276be49a6ce1bd8e15 | byte-exact vs all pins; audit PASS (Verifier r23); ready for Arnold exec from shared root |
| memory/llm/hosts.md | 16,386 B | 9aef7fe139741efcaf58ddd700d02522 | byte-exact vs Verifier pin; NEXT item CLOSED on disk (Mechanic + Archivist concur) |
| memory/llm/instances.md | 3,752 B | d1c1d38e3adc2ac18f3763d8aff1cddf (mtime 03:16) | content PASS (Scribe: all four r21 patch points); hash drift — see flag F2 |
| memory/verifier/_canary_remote.txt | — | — | ABSENT → AC-A2-2 LIVE still blocked at canary relay (owner: Verifier) |

## Flags (evidence vs claim; no picks made)
- **F1 — Builder's r22 repin reverted/unproven.** Builder reports root re-pinned 9c6b08e3→8ef4e2227a7afd506ed2b55dc9dd170d via `repin_root_index.py` (717368ae, confirmed present in memory/builder/). Disk now shows PRE-SWAP 9c6b08e3; Verifier independently observed Black seat hold 8ef4e222 then regress to 9c6b08e3. Consistent reading: a later mirror/sync pass clobbered the repin (or it never reached this root). Builder's evidence leaf `index-repin-r22-*.md` was NEVER written (absent from memory/builder/; his farm569 closeout predates the repin and omits it). → Action: Builder/Orchestrator owe White-side canonical restamp + new evidence leaf before the WCAG-A fix counts as landed. Confidence in revert reading: HIGH (two independent seats + root disk all show pre-swap bytes).
- **F2 — instances.md pin conflict is a RECORD discrepancy, not content loss.** Disk = d1c1d38e / 3,752 B. Claimed pins disagree with each other AND with disk: Archivist (this round) cites r21 pin 27ffbd6b / 3,788 B; Scribe cites "Archivist's claimed pin 609f1d6d / 3,753 B". Neither matches current disk. → Action: Archivist to state which claim was which round and re-pin d1c1d38e as the live hash.
- **F3 — Designer's `panel-discipline-r20.md` not observed.** Claimed created (outside-click adoption, 4-line JS insertion + 5 ACs) but absent from memory/designer/ at sweep time. Transport line says new files propagate; if it exists on his seat it should land within mirror cadence. → Action: Designer to confirm/re-write; until then the outside-click patch is unapplied-and-unrecorded (Builder cannot hash-gate a file that isn't there).
- **F4 — N re-pin basis is White-local.** Shared-root uploads/ = 1 entry (DCABOTS-MOVED.md, 189 B); Verifier's "3 non-canary entries today" refers to White's local uploads/, invisible from this seat. N=1 re-pin remains a Verifier+Arnold leg.

## Chain state (unchanged owners)
Verifier: relay `_canary_remote.txt` (212 B / 512d0dc8e96773b7db5574da4f0ae9f3) to propagating path + re-pin N → Arnold (White console): canary placement + WCAG-AA one-shot (re-run after F1 restamp) + `python memory\mechanic\ac_a2_live_leg_r20.py` → Verifier accepts. AC-A2-1/3/4 CLOSED; A2-2 static CLOSED; sole surviving sub-clause = A2-2 LIVE.
