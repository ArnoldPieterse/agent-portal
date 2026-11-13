# Synthesis — White rename closeout + r20/r21 verification round (2026-11-14)

Scribe record. Every line traces to a named source in this thread or TODO.md LIVE PLAN. Round ended with all seven agents [CONCLUDED]; surviving items are named handoffs only.

## Decided (one-line rationale each)
1. **White rename RESOLVED 01:45, panel verified** — live state = Q4_K_S from `unsloth\Qwen3.8-27B-GGUF` (ctx 131072) + Q8_0 from `lmstudio-community\Qwen3.8-27B-GGUF` (ctx 32768), both reporting under bare id `Qwen3.8-27B-GGUF`, so the count-based guard is the only reliable check for White. *(TODO.md OPS NOTE 01:1x; Orchestrator re-verify this round)*
2. **recover_all.py dual-path safe** — `_resolve()` prefers new name, falls back to old; `dual_ok()` accepts either cmdline form → boot recovery works pre- and post-rename; py_compile OK ×3 (fleet_reload.py, recover_all.py, reboot_launchers.py). *(TODO.md OPS NOTE; Builder closeout leaf)*
3. **v1 run ABORT_unload 01:15:01 was correct to abort** — unload body sent `{'id':...}` but endpoint requires `model_path` (422 ×11); v2 fixes = unload by full path first, then remaining by reported id; load order Q8 FIRST then Q4. *(TODO.md OPS NOTE)*
4. **hosts.md White-line TODO item is DONE on disk** — Researcher's corrected "White model folders → fleet convention" section (quant-named paths, lines 20–24); Verifier rename-consistency check passed (hosts.md 9aef7fe1); Mechanic + Archivist independently confirmed the checkbox is stale → safe to strike. *(Verifier r21 sweep; Builder closeout; Archivist r21 addendum)*
5. **AC-A2 closed except the live leg** — AC-A2-2 stays OPEN on a single pass (N=1 row / raw 200 / exactly 212 B / md5 prefix 512d0dc8), blocked solely on `ac_a2_live_leg_r20.py` bytes, verified absent from White shared root by three independent full-tree walks (Orchestrator host clock 03:06; Researcher ~03:05; Verifier ~04:05). *(Orchestrator escalation line in TODO.md top; Researcher r20 lane leaf; Verifier r21 sweep)*
6. **instances.md r21 patch had not persisted** — disk on White canonical was back at pre-patch 297d286e / 3,413 B with quant-less alias paths; Archivist re-applied per spec → new pin **609f1d6d / 3,753 B** (header date 11-14, L13/L14 post-rename folders, attribution note, L5 ctx 65536→131072 annotation). Verifier's in-transit flag (his seat still pre-patch) stands until propagation; hash confirmation owed then. *(Archivist r21 addendum; Verifier r21 sweep)*
7. **WCAG-AA audit of pinned canonical index.html: exactly one real miss** — `.aev .at` agent-event timestamp at 3.47:1 on `--panel2` (small text, AA 4.5:1 applies) in canonical 9c6b08e3 / 67,681 B; fix staged as one-line palette swap `#6b7688`→`#8b93a7` (worst case 5.18:1) in `designer/staged/variant_8ef4e2227a7a.html` (md5 8ef4e2227a7afd506ed2b55dc9dd170d). P1 native `alert()`/`confirm()` debt (L326, L906–923) stays a separate change per one-concern-per-pin. *(Designer r5 canonical audit leaf)*
8. **Fleet health from Red 03:10** — Black .99 and Pale .39 both DUAL-RESIDENT, all four aliases loaded (Q4_K_S ctx 65536 + Q8_0 ctx 32768 each); White .179 unreachable from Red (:8888/:8099 timeout; SMB C$ error 5) → White ground truth = mirror copy of canonical TODO.md + indirect proof the portal is up (this chat routes through it). *(Mechanic probe_fleet_1114b_result.json + runbook leaf)*

## Still open (owner)
- `ac_a2_live_leg_r20.py` re-stage or relay byte-exact via portal drop — **Mechanic** (TODO.md top line; do NOT retype from the 2,341 B / 49-line summary); Arnold confirms presence at White root before running; Verifier pre-run audit + pin unchanged.
- Strike MEMORY.md GOAL line "Verifier closes AC-A2-1..4" — **Orchestrator** (per Verifier r20 bottom-line).
- dcabots re-prompt (only Orchestrator's turn failed) + E14 White-console run + console-clean browser leg + ~39 GB cleanup candidates — **Orchestrator / Arnold / human**.
- smoke8 outside an active turn, via White-console human leg (chat sits on quinn-q4; mid-turn smoke risks wedge #2) — **Mechanic via human**.
- Apply Designer variant + re-pin as new canonical — **Orchestrator/Builder**.
- O4 farm.py:569 re-run — **Builder**, awaits White-console apply + patched-file handoff.

## Contradictions / evidence flags (no silent picks)
- No agent-vs-agent contradiction this round. Two evidence flags: (a) instances.md hash divergence Verifier-seat 297d286e vs Archivist r21 claim — resolved by re-apply to 609f1d6d, propagation confirmation still owed; (b) Designer's python-sandbox view of root index.html flapped across three byte views in ~3 min (incl. same md5 at two different sizes = mid-read swap) while Z:\ terminal read was stable 3/3 — fresh data point for the stale-root read degradation family Verifier ruled on in r15-v, now observed on a root doc from Designer's own tools; Mechanic/Verifier to fold into skew diagnosis.

## Lane status at round end
Orchestrator / Researcher / Builder / Verifier / Designer / Archivist / Mechanic: all [CONCLUDED] with evidence leaves on disk. Nothing owed from Scribe beyond this record.
