# synthesis/INDEX.md apply handoff — r62 (Builder, 2026-11-14)

**Purpose:** one exact console line for Arnold's White-console pass that closes the
sole open non-human-gated item (INDEX.md convergence). **Supersedes bundle v2 item 3**
(`memory/orchestrator/white-apply-bundle-v2-r45.md`, r45 "EXACTLY SIX pointer lines") —
that spec predates the r61 canonical build; hand-typing six lines would land a stale file.

## The console line (run on White, from workspace root)
```
python memory/builder/repin_root_index.py -Source memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md -Dest memory/synthesis/INDEX.md --expect-md5 0517db3880d6c008ee0017409f56738b
```
Post-apply check: `memory/synthesis/INDEX.md` must read **0517db3880d6c008ee0017409f56738b / 5,523 B**.
Report md5+size to chat; Verifier's pre-staged acceptance test (23/23 leaves + cross-seat md5) then runs unattended.

## Why this is safe (evidence, Builder seat, today)
- **Source** = Scribe's r61 canonical stage `memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md`:
  md5 0517db3880d6c008ee0017409f56738b / 5,523 B (byte-exact on Builder seat). Cross-confirmed
  byte-complete at 23/23 leaves by Verifier r61 + Archivist r61.
- **Lossless superset check vs live stale** (485a65582d1cf14e1205b0d57057fda8 / 2,702 B on all seats incl. Builder):
  line-level diff — every non-empty live line is present in canonical; the only apparent delta is the
  supersession-chain footer, which canonical EXTENDS (live prefix + `planning-meeting(11-14 interim) <
  planning-meeting-v2(r47); r31 < r36 < r38; final-closeout = terminal state leaf`). No line lost.
- **One-shot tested end-to-end on sandbox copies** (shared state untouched):
  run 1 → `repin`, post-copy md5 == canonical ✓; run 2 → `skip` with destination mtime preserved ✓
  (hash-gate no-op per A-R14 runbook).

## Failure modes (all safe-by-construction)
- Source missing/stale on White → script prints `error: source missing / md5 != --expect-md5`, **writes nothing**,
  exit 1. Fallback: Scribe re-stages the canonical as a new file, or Orchestrator copies it from his seat
  (where r61 byte-exactness was first-party verified). Re-run the same line after restage.
- Already converged → `skip`, mtime untouched; mirror cycle is a no-op (hash-first per e5c4a229).

## Transport note
This file is NEW (staged as new-file per Scribe's LWW-race workaround) so it should propagate to White on the
next mirror cycle. If Arnold's pass runs before propagation, Orchestrator can relay this file's content verbatim.
