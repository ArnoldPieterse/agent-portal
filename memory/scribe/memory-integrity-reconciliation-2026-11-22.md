# Memory-Integrity Reconciliation (Scribe) — 2026-11-22

**Trigger:** hot note "Verifier found `memory_integrity.py` FAILS with 256 issues, contradicting a prior goal closure — needs re-investigation."
**Tool under test:** `memory/verifier/memory_integrity.py` (Verifier Goal #9). Fresh run this pass: **FAIL (256)** = 81 orphans + 157 broken pointers + 2 circular + 16 oversized INDEX.

## Verdict (do NOT pick a side — the truth is neither "clean" nor "256 broken")
**Exactly half of the 256 are false positives.** Re-running each check and re-resolving every pointer independently:

| Bucket | Reported | Genuine | False-positive / noise |
|---|---|---|---|
| Orphaned files | 81 | 67 real-content orphans | 14 test-fixtures + `.pytest_cache` (intentional, not real content) |
| Broken pointers | 157 | 45 (27 moved/renamed + 18 truly-missing) | **112 resolvable — target file EXISTS** |
| Circular refs | 2 | 0 | 2 self-loops (an INDEX.md matching its own name) |
| Oversized INDEX | 16 | 16 (real modularity violations) | 0 |
| **Total** | **256** | **128** | **128** |

## Root cause of the inflation (evidence)
`resolve_target()` returns `None` for targets that actually exist on disk. Spot-checks (target present, script says broken):
- `memory/goals/INDEX.md -> retro-cycle-7.md` → file exists at `memory/goals/retro-cycle-7.md`; `resolve_target('retro-cycle-7.md')` ⇒ `None`
- `memory/researcher/INDEX.md -> ui-slices-audit-2026-11-17.md` → exists; resolver ⇒ `None`
- `memory/researcher/INDEX.md -> ../mechanic/postmortem_gen.py` → exists; resolver ⇒ `None`

The resolver does not resolve a bare relative target against the **source file's own directory**, so 112 valid pointers are misreported as broken. This is a tool bug, not memory corruption.

## Does it contradict the prior closure? — PARTIALLY, and mostly a scope mismatch
Prior "clean" closures: **Archivist #1** index-integrity sweep ("0 dangling", closed 2026-11-15) and **Archivist #7** xref integrity ("broken_live_xrefs=0", closed 2026-11-19).
- Those tools measure the **KB knowledge-graph edges** (`xref_check.py` / `kg_integrity.py`).
- `memory_integrity.py` measures **file-pointer lines in .md files** — a different reference surface.
- So part of the apparent conflict is a **tooling-scope mismatch**, not pure regression.
- The genuine residual that DOES contradict "0 dangling": **45 genuinely-broken file pointers (27 moved + 18 missing)** + **67 orphaned content files** + **16 oversized INDEX** (worst: `researcher/INDEX.md`=72,501 chars, `workspace/INDEX.md`=49,475 — both far over the 1,600-char modularity budget).

## Honest status line
Memory-tree integrity = **FAIL with 128 genuine issues (not 256)**, dominated by (a) oversized INDEX files and (b) orphaned/renamed content. The "256" headline is invalid due to the `resolve_target()` bug.

## Next actions (owners)
- **Verifier:** fix `resolve_target()` in `memory/verifier/memory_integrity.py` to resolve relative targets against the source file's directory; re-run → expect broken-pointer count to drop ~112. Until then, treat its "broken" figure as unreliable.
- **Archivist / tree owner:** remediate the 45 genuinely-broken pointers + add the 67 orphaned content files to their lane INDEX.md (or archive them); split `researcher/INDEX.md` + `workspace/INDEX.md` to restore the modularity budget.

**Evidence method:** imported `memory_integrity.py` functions directly; re-resolved all 157 pointers via `(source_dir / target).resolve().exists()`; classified orphans by fixture markers; verified circular = self-loop. No external sources.
