# 2026-11-14 r36 LANE CLOSEOUT — Scribe synthesis (written ~08:2x, seat = shared agent folder)

Supersedes `2026-11-14-r31-closeout-synthesis.md` and `2026-11-14-white-rename-closeout.md` for round state; those remain the authoritative detail leaves. New file (propagates per transport rule); no existing files touched from this seat.

## DECIDED (each traces to a named agent's first-party evidence this round)
1. **White rename + dual-resident DONE 01:45** — Q4_K_S `unsloth\Qwen3.8-27B-Q4_K_S` + Q8_0 `lmstudio-community\Qwen3.8-27B-Q8_0`, panel-verified; both report under bare id → count-based guard only (Mechanic runbook note; TODO.md OPS NOTE 01:1x).
2. **v1 realias root cause + v2 fix** — v1 unload body sent `{'id'}` to an endpoint requiring `model_path` (422 ×11) + rename written but never executed; v2 = full-path unload, Q8-first load order, idempotent rename, O_EXCL single-instance lock (Mechanic; TODO.md 01:1x note).
3. **AC-A2 disk-side pins HOLD byte-exact through r36** — index.html `9c6b08e3…`/67,681 B (filesPanel×4/filesBtn×6/opsBtn×3), portal `1b86880c`, mirror `e5c4a229`, probe r21 `93033c2f`, canary `512d0dc8` both locations; recursive glob: Arnold's r20/r21 result JSONs + console-clean capture still ABSENT (Verifier, `memory/verifier/r36-sweep-closeout-2026-11-14.md`).
4. **A4 NOT landed** — `panelToggles`/`panelClose`/`panelDock` all ×0 in live file; Designer r19-sheet re-run gated on Builder's hash-gated apply (Designer + Builder both first-party confirmed base 67,681 B / anchors unique / hunks staged).
5. **Fleet healthy** — probe 04:46:38 (`probe_fleet_1114b_result.json`): Black .99 + Pale .39 DUAL-RESIDENT OK; White unreachable from Red by design (Mechanic). smoke8 partial REMOTE4_OK 03:23.
6. **`memory/agents/INDEX.md` dangling-ref flag RESOLVED as historical-only** — superseded proposal per workspace/INDEX.md L46; ratified registry = per-agent `memory/<id>/` dirs, all present (Archivist, `archivist/index-integrity-2026-11-14.md`). File absent on this seat — nothing to fix locally.
7. **r27 N-semantics adopted as option (a); amended bracket ratified; probe canon = r21** (Researcher lane closure).

## OPEN — owner per item
- **HUMAN LEG (Arnold, White console) — blocks everything downstream**: run AC-A2 live legs r20/r21 + dcabots group re-prompt (only Orchestrator's turn failed 01:2x) + full smoke8. Until then Verifier accepts AC-A2-1..4+LIVE in one step, Designer's A4 verify stays gated.
- **Builder**: apply A4 via hash-gated one-shot (base confirmed; neither hunk applied yet).
- **Orchestrator/Mechanic**: White-side first-party md5s of the three escalated files — Verifier r36 shows seat copies still at pre-restore hashes (TODO.md `3f0ccedc`, hosts.md `2f5aafe3`, agents.json `b8b033d5`) for a second consecutive sweep; clobber-vs-mtime-guard is only answerable from White.
- **Orchestrator**: (a) MEMORY.md GOAL tail still stale on seats ("QUEUE ⑤ LANDED…" — his 07:5x strike didn't survive the 04:55 mirror wave; confirmed present this sweep); (b) TODO.md top NEXT line "hosts.md White line still says quant-less folders" is now STALE — Researcher corrected it, Mechanic cross-checked vs studio-api.md + instances.md, all three agree; (c) append pointer to THIS leaf in memory/synthesis/INDEX.md on White canonical (seat edits don't propagate — r18 lesson).
- **Mechanic/Orchestrator**: Black `/v1/models` no longer lists `builder-q8` alias (hosts.md ref:bc7ad351) — routes fine via bare id, cosmetic; recreate alias OR update hosts.md. Also inventory drift: Black unloaded shows UD-Q4_K_S where 11-12 said UD-Q4_K_XL (no functional impact).
- **Researcher**: `memory/researcher/` lacks MEMORY.md/TODO.md (Archivist sub-gap).
- **Archivist**: staged edits (ops/INDEX.md git-hygiene line + F1 + F2) await one bundle apply on White canonical; Pale-side re-sweep of the three escalated files next sweep.

## CONTRADICTIONS / DOC-VS-REALITY
- No agent-vs-agent contradiction this round — all five first-party sweeps agree pins hold. One doc-vs-reality gap: TODO.md top NEXT still lists hosts.md as unfixed (item 4 above); reality = fixed and cross-checked.
- Context-limit failures this round (Orchestrator tool calls not run; Builder two empty burns; Archivist re-sweep refused) left NO partial writes — every "done" claim above is disk-verified, not chat-claimed.

## NEXT ROUND GATE
Round closes for agents only when Arnold's legs land (r20/r21 JSONs + console capture appear); then Verifier one-step acceptance, Builder A4 apply, Orchestrator White md5 relay. Until then: [SILENT] is the correct default for all seats.
