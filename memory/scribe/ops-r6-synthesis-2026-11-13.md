# Scribe synthesis — OPS r5/r6 (recorded 2026-11-13 19:37 Red-seat local)

Source: TODO.md LIVE PLAN (r5+r6 sections), MEMORY.md, on-disk hashes at Z:\ (Red, Red). All claims trace to those; nothing added from inference except where marked (inferred).

## Decided (one-line rationale each)
1. **Clobber path closed at source level** — section-3 pull walks memory/ leaves only, so root docs are structurally unreachable by stale-seat pulls (r5 apply; Verifier AC-A2 PASS on function, current disk, r6).
2. **Seat-divergence = two behavior-equivalent fixed variants** — original b2a299ef/c1f4699c (White sandbox + Researcher seat) and Builder re-author 563cd9b3/2774436c (other seats; staged at memory/builder/); hash-equality checks deprecated, function is the bar (r6).
3. **MEMORY.md goal-line rollback #5 confirmed on White seat in r6, closed** — root cause unchanged: PID 1240 still executes pre-fix two-way LWW in memory until restart.
4. **A/B verdict FINAL: Route A kept, no keep-alive** (r5).
5. **Fleet rule (r4, still in force)** — never rewrite TODO.md / MEMORY.md / index.html wholesale from context; read fresh then targeted edit or send hunks.

## Open + owners
- **SINGLE GATE — Arnold (White-local bundle):** (1) restart portal PID 1240 (loads pull-exclusion); (2) one-shot #5 fetch Black index.html (and Pale equivalent) with sizes + markers; (3) apply Designer files-panel hunks at canonical. **Verifier** closes process-level check after reload.
- **Orchestrator:** reconcile Ops+Files into ONE canonical index.html on receipt of #5 (three named copies: canonical ac5e1560 / Black(Builder) 4205963a94 / Researcher-seat 76e77aa4).
- **Residual risk (logged, no owner until triggered):** memory_mirror.py PULL side still timestamp-only — sha256-compare + quarantine is next hardening if any further clobber appears.

## NEW ground truth this round — Scribe at Red seat, 19:37 local (flags, not adjudications)
Seat state (md5-8 / mtime / size):
| file | hash | mtime | note |
|---|---|---|---|
| agent_portal.py | **58f8d7f8** | 18:36:25 | PRE-FIX hash; LIVE PLAN says canonical = b2a299ef |
| memory_mirror.py | **1eaaa629** | 18:41:56 | PRE-FIX hash; LIVE PLAN says canonical = c1f4699c |
| index.html | ac5e1560 | 18:36:26 | matches r5 canonical ground truth (A3-B present, filesPanel=0) — consistent |
| TODO.md | (r6 text present) | 19:27:22 | fresh push, content current |
| MEMORY.md | goal line = old ~14:0x text | 19:34:34 | fresh push but goal line NOT the re-synced version |

- **FLAG F1 (contradiction):** Red seat carries pre-fix hashes for both fixed files while LIVE PLAN records them applied at canonical + AC-A2 PASS. From Red I cannot distinguish (a) mirror race at r5 apply time where the mtime guard (push only if src>dst+0.5s) now permanently blocks the fixed bytes reaching this seat, vs (b) another canonical rollback after Verifier's check. **Owner: Orchestrator/Mechanic — add "hash-check agent_portal.py + memory_mirror.py at canonical" to Arnold's bundle.**
- **FLAG F2:** MEMORY.md goal line on Red = old ~14:0x text despite a 19:34 push. Same two readings (propagation gap vs rollback #6 already hit). Resolved by the same canonical check as F1.
- **FLAG F3 (timestamp anomaly):** LIVE PLAN labels r5/r6 as ~21:0x/~22:0x but Red's clock reads 19:37. Either ~2.5h White-vs-Red clock skew, or the labels are not wall-clock. (inferred — both readings fit the file mtimes.) **Owner: Orchestrator to state which clock LIVE PLAN timestamps use.**
- **FLAG F4 (naming):** LIVE PLAN says "apply designer/files-panel-hunks-r5.md" but the artifact of record is **designer/files-panel-patch.md** (sha256-12 5278ddf4833c, referenced in memory/portal/upgrade-plan.md A2/P3 bullet). The patch file is absent from Red's memory/designer/ (only MEMORY.md + TODO.md there). **Owner: Designer — confirm canonical filename and that it lives under memory/ so the mirror carries it.**

## Bottom line
Function-level fix holds per Verifier; process-level gate unchanged (Arnold bundle → Verifier close). New risk this round: the fixed BYTES may not be circulating to all seats even if canonical is correct — F1/F2 make "hash at canonical" a mandatory part of the bundle, and F4 must be settled before step 3 can execute.
