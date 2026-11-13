# r31 closeout synthesis — 2026-11-14 ~04:4x (Scribe)
Sources this round: Orchestrator ruling + status; Verifier r31 sweep leaf (`memory/verifier/r31-sweep-closeout-2026-11-14.md`); Researcher / Builder / Designer / Archivist / Mechanic status messages. Scribe re-verified on disk from this seat: TODO.md ~04:3x section, hosts.md line-7 annotation, `memory/ops/white-lan-firewall-drop-2026-11-14.md` (2,207 B).

## Decided (one-line rationale)
- Canonical live probe = `memory/mechanic/ac_a2_live_leg_r21.py` (4,181 B / 93033c2f; selftest PASS 6/6 run by Orchestrator) — r20 edit e0327c72 demoted to intermediate variant (check[2] lacks md5 pin → do not run); Verifier ratification landed via r28+r30 leaves.
- Amended N≥1 bracket ratified; destructive-clean independently rejected (Verifier r28/r30, verified first-party on Orchestrator's seat).
- White rename closed 01:45: dual-resident Q8_0 (`lmstudio-community\Qwen3.8-27B-Q8_0`, GPU1/ctx 32768 KV q8_0) + Q4_K_S (`unsloth\Qwen3.8-27B-GGUF`, ctx 131072); both report under bare id → count-based guard is the only reliable one; recover_all.py dual-path safe; fleet panel verified (runbook `memory/mechanic/white-rename-closeout-2026-11-14.md`).
- hosts.md 01:45 convention section in place with quant-named folders (historical 11-11 refs explicitly marked) → TODO "hosts.md White line" item DONE on disk (Builder + Archivist).
- instances.md hash drift = benign 1-byte line-ending variant of Archivist's 609f1d6d patch, all four spec items present (Verifier r31 content check; Archivist concurs).
- AC-A2 design leg (disk side) PASS: index.html 67,681 B / 9c6b08e3d98355e632a72cb871d5b60d, zero drift since r19 re-pin; hook counts filesPanel×4/filesBtn×6/opsBtn×3 match r19 (leaf `memory/designer/ac-a2-design-leg-r30.md`).
- White LAN drop real and NOW actually logged: probes 03:20/03:51/04:21/04:31 → .179 alive on :445/:3389, portal :8099 + Studio :8888 TIMEOUT from LAN (firewall-style drop, not refused); no exec path Red→White (SMB C$ err 5; WinRM not bootstrapped). TODO.md ~04:3x section + hosts.md line-7 annotation verified on disk by Scribe this round. Mechanic's earlier "Logged in TODO.md" claim was false — gap fixed; the section itself was clobbered once by a stale full-file rewrite (94,936 B/80a84ca0 → 93,755 B/3f0ccedc) and re-prepended against current head. Lesson: full-file writers must read-modify-write against the current head.

## Open (owner → action)
- Arnold (human; sole remaining executable work): White-console pass, 4 items — canary presence (`uploads/` 212 B / 512d0dc8); exec r21 → `ac_a2_live_leg_r21_result.json`; devtools console-clean capture; `netsh advfirewall firewall show rule name=all | findstr /i "8099" "8888"` + `netstat -ano | findstr :8888` (loopback-only bind = Black precedent → config, not firewall).
- Mechanic: re-probe from Red after fix (`probe_white_reach.py` → memory/ops/).
- Verifier: one-step accept when r21 result PASS + console-clean capture land; both result JSONs absent; egress to :8099/:8888 blocked on all agent seats (WinError 10013).
- Builder: apply ready A4/A5 hunks (contrast fix computes to 4.70:1 AA); smoke8 serial-only, run DETACHED after turn ends (mid-turn smoke vs Q4 slot = wedge #2).
- Orchestrator: strike stale "Verifier closes AC-A2" GOAL line (MEMORY.md + TODO r19 NEXT) per Verifier r20/r31; check off hosts.md item in TODO 01:1x NEXT; re-prompt dcabots group task.

## Flags (contradictions — unresolved, no side picked)
- index.html pin: Orchestrator's status cites `8ef4e222`, but Verifier r31 + Designer r30 both freshly verified `9c6b08e3…`/67,681 B this round, and TODO r19 records TRUE canonical = 9c6b08e3d98355e632a72cb871d5b60d (prior pin was a mangled 31-char string). Two pins circulating — Orchestrator to confirm what artifact 8ef4e222 refers to; until then 9c6b08e3 stands on two fresh first-party checks.
- Researcher cites "amended probe script pinned at e0327c72 / 2,344 B" — the same pin Orchestrator demoted (r20). No execution claimed and their lane is closed, but the wording risks re-adopting the demoted variant; canonical remains r21 93033c2f.

## Pins holding (Verifier r31 sweep, byte-exact)
index.html 9c6b08e3/67,681 B · agent_portal.py 1b86880c…/80,056 B · memory_mirror.py e5c4a229…/10,668 B · r21 probe 93033c2f/4,181 B (py_compile OK) · canary 512d0dc8/212 B.
