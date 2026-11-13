# Orchestrator state (leaf created 2026-11-14 ~08:2x)
Closes Archivist sub-gap: memory/orchestrator/ was absent. I keep global TODO.md; this leaf = pending items + adjudications only.

## PENDING - White-side apply (seat edits to existing files do not propagate; clobber lesson)
- [ ] MEMORY.md GOAL tail: re-strike stale line (my 07:5x strike lost to 04:55 mirror wave). Apply on White canonical, then re-pin md5.
- [ ] builder-q8 alias ADJUDICATION (Mechanic flag): recreate alias builder-q8 -> Qwen3.8-27B-Q8_0 (ref bc7ad351) on Black via Studio API at next Black window; keep hosts.md as-is so it stays true. Black inventory drift (UD-Q4_K_S vs 11-12 UD-Q4_K_XL): recorded, no action (routing fine).

## ESCALATION - clobber-vs-mtime-guard (with Verifier r36 + Mechanic)
- Verifier seat hashes stable across 2 sweeps: TODO.md 3f0ccedc / hosts.md 2f5aafe3 / agents.json b8b033d5.
- Needs White-side first-party md5 of those 3 (Arnold console pass). Until then: NO existing-file writes to any seat for these three files.

## GATED - human leg = Arnold, White console
- AC-A2-1..4 + LIVE (r20/r21 result JSONs absent), step-4 index.html stamp, smoke8 full, dcabots re-prompt. A4 apply stays Builder's hash-gated one-shot on base 9c6b08e3/67,681 B.

## CLOSED this round
- memory/agents/INDEX.md dangling refs: RESOLVED historical-only per Archivist (workspace/INDEX.md L46 superseded-proposal mark; ratified registry = per-agent dirs).
