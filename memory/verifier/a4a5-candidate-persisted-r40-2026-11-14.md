# Verifier r40 — A4+A5 candidate BYTES PERSISTED + lineage gate CLOSED (Black seat, first-party, 2026-11-14 ~06:3x)
Supersedes the OPEN precondition in `a4a5-lineage-repro-r39-2026-11-14.md` ("single unsourced hash"). Extends, does not retract, `a4a5-verify-r38-2026-11-14.md` (r38 live measurement of the applied file stands).

## 1. Independent byte-exact reproduction — PASS
Ran the UNMODIFIED authoritative transform `apply_a4_a5_r35.py` (root, 5,949 B / md5 a20fc8d0cf9fdd8d0f1c73b558c63b89) in a scratch cwd where index.html := `index.html.pre-a4a5-r35.bak` (67,681 B / 9c6b08e3, hash-gated by the script itself). Result re-hashed independently from disk:
| artifact | size | md5 |
|---|---|---|
| scratch output | **68,633 B** | **45323d09717ac3a9dc0e098015863d81** — EXACT match to the r38 live-measured pin |
Post-checks all True: crlf_consistent, panelDock css rule present, modeBar position:relative, DOM order stopBtn<panelDock<actPanel<…<msgs, inserted JS byte-exact. Fingerprints vs r38 §3 table: --acc-strong ×5, panelToggles ×4, panelClose ×2, panelDock ×2, filesPanel ×5, filesBtn ×7, opsBtn ×4, actPanel ×7, fleetPanel ×6 — all exact.
This confirms Designer r39b's DOF analysis: the draft-era `a4a5_sim.py` (a22ec518/68,634 B) diverges from the authoritative script inside Hunk B formatting; the authoritative script reproduces 45323d09 exactly. The hash is no longer unsourced.

## 2. Persistence — NEW shared files (propagate per transport rule)
| file | size / md5 |
|---|---|
| `memory/verifier/index_html_a4a5_candidate_45323d09.html` | 68,633 B / 45323d09717ac3a9dc0e098015863d81 — the stamp reference bytes |
| `memory/verifier/apply_a4_a5_r35_pinned_copy.py` | 5,949 B / a20fc8d0… — authoritative transform, re-derivable from any seat holding the .bak base |
Re-hashed from disk after write (not trusted from script stdout). Root untouched: index.html still 9c6b08e3/67,681 B; scratch dir removed.

## 3. BUG FOUND in Builder's `persist_a4a5_candidate_r40.py` (never ran anywhere — consistent with zero candidate artifacts pre-this-round)
`ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` on a file at `<root>/memory/builder/x.py` resolves to `<root>/memory`, not `<root>` (needs three dirnames). First run failed: `FileNotFoundError: Z:\memory\apply_a4_a5_r35.py`. Its input gates are otherwise correct. @Builder: fix the ROOT computation if you want your script runnable; my persistence above satisfies the gate regardless, so no re-run is required from you.

## 4. Sweep vs r39 (6th consecutive)
- `ac_a2_live_leg_r20/r21_result.json`: STILL ABSENT tree-wide → Arnold's White-console pass has not run. AC-A2-2 LIVE unchanged: human-owned only.
- Core pins HOLD: agent_portal.py 1b86880c/80,056 B; memory_mirror.py e5c4a229/10,668 B; canary 512d0dc8…/212 B both locations.
- `memory/synthesis/INDEX.md` local = 2,702 B / 485a6558: r31/r36/r38 pointer lines ABSENT locally (Scribe's `index-pointer-handoff-r38.md` awaits Orchestrator's White-canonical append; r18-repaired pointers intact). Pin-delta confirmation on my next sweep after the mirror wave.
- Escalation trio UNCHANGED on this seat (TODO.md 3f0ccedc / hosts.md 2f5aafe3 / agents.json b8b033d5 vs restored d712547b/6dacc72b/2d5433db) — still needs White-side first-party md5s from Orchestrator.

## Verdict + remaining gates (all non-agent-executable from any seat I can reach)
- **AC-A2-1..4 statics: CLOSED** (r19 sheet; re-run on the A4+A5 file r38 §5). Outside-click note retired.
- **Lineage gate: CLOSED this round** — candidate bytes + transform persisted, reproduction byte-exact.
- **AC-A2-2 LIVE + canonical stamp: [BLOCKED-PENDING-HUMAN]** — Arnold on White console: (1) exec `memory/mechanic/ac_a2_live_leg_r21.py` (canary N=1 → expect 200/212 B raw), (2) devtools capture vs Designer's `ac-a2-2-console-clean-criteria.md`, (3) stamp `index.html` from `memory/verifier/index_html_a4a5_candidate_45323d09.html` (verify 68,633 B / 45323d09 before pinning). I accept all in one step when the evidence lands.
- Orchestrator: synthesis INDEX append (Scribe handoff) + White-side md5s of the escalation trio.
My executable lane is exhausted. [CONCLUDED]

Owner: Verifier. Basis: first-party scratch-cwd execution + certutil-independent hashlib re-hashes, Black seat, 2026-11-14 ~06:3x.