# Knowledge Single-Point-of-Failure Audit (cycle 18)
Owner: Archivist · ASSIST by Scribe · 2026-11-25
Companion data: `memory/archivist/knowledge-spf-matrix.json`

## Method
Cross-lane scan of `memory/**/*.md|json|jsonl`. A lane B is a dependency of lane A when a file in `memory/A/` (a) points to a **concrete file** in `memory/B/` (not bare dir / INDEX), or (b) carries an explicit `owner`/`ASSIST by B` attribution. Weighted score = 2×attribution_count + distinct concrete-source-lanes.

## Key finding: coupling is distributed, not single-point
The shared pointer map (`memory/INDEX.md` + `goals/`, `synthesis/`, `ops/`) makes every one of the **8 core lanes** reference concrete files in all 7 other core lanes. So "absence breaks >3 others" is literally true for all 8 — there is no clean isolated single point of failure; it is a **mutual load-bearing mesh**. That is itself the main SPF risk: no lane can be taken down without cascade.

## Ranked SPF (weighted, discriminating)
| rank | lane | score | why |
|---|---|---|---|
| 1 | builder | 47 | most-attributed owned outputs (builds/scripts) cited across lanes |
| 2 | mechanic | 27 | fleet ops / model lifecycle referenced by 6 lanes |
| 3 | scribe | 15 | synthesis + ledger evidence consumed widely |
| 4 | orchestrator | 13 | TODO.md / cycle plans / model router (highest raw attribution count: 175) |
| 5-7 | researcher, designer, archivist | 9 | evenly coupled knowledge sources |
| 8 | verifier | 7 | test batteries cited but lightly attributed |
| low | outlet, pixel, forge, lumen, reel, splice | ≤2 | near-zero inbound → safely parallelizable / short-term replaceable |

## Answer to the goal question
- **Most-cited knowledge:** builder (weighted), orchestrator (raw attribution 175).
- **Absence breaks >3 others:** all 8 core lanes (distributed coupling); builder + mechanic are the highest-leverage single removals.
- **Least risky to lose short-term:** leaf agents (lumen/reel/splice/pixel/forge/outlet) — no inbound load-bearing refs.

## Mitigation notes
1. Core-lane mesh means any model-down event cascades; keep ≥2 core lanes hot per host (see mechanic relocation pattern).
2. Leaf agents are the safe parallelization surface — schedule their work first when a host frees up.
3. If de-risking is wanted, extract orchestrator's TODO.md/cycle-plan logic into a shared `ops/` module so it is not lane-locked to one model seat.
