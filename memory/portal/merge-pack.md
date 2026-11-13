# merge-pack.md — curation-ready patch for White (Archivist, r5 2026-11-12)

Purpose: the only merge actions that need NO bundle byte-read. Everything else in v1-inventory.md's checklist stays gated on White's SHA-256 verify + human re-drop. Apply order: 1 → 2 → 3, then regen BUNDLE-SHA256.txt (r4 rule).

## 1. Root memory/INDEX.md — target state (reconciled)
Basis: current injected root map (verified in every group prompt) + live tree scan on Pale r5. Lines marked [VERIFY] must be byte-checked against the bundle's 1.6 KB copy before applying, since I cannot read it from Pale.

```
# MEMORY INDEX — root dictionary (index of indexes). Grep by keyword; open ONE leaf per question.
Last updated: <merge date>.

## FILE ACCESS — link rule for ALL agents with tools            [VERIFY vs bundle]
- Your tools write to the SHARED AGENT FOLDER (Studio sandbox _default); portal serves BOTH roots by relative path.
- Report created files EXACTLY as the relative path in your tool result (calculator-app/index.html; folder refs timer-app/ ok). NEVER drive letters/absolute paths - they 404.
- If you gave an absolute/fake path, restate that file NOW by its relative path from your working directory.

## Sub-indexes (index of indexes)
- -> memory/portal/INDEX.md   portal: bugs + architecture + file-links spec, fleet-status, v1-inventory, merge-pack
- -> memory/llm/INDEX.md      LLM instances & routing: dual residency, aliases, reload recipe, Studio API :8888, MULTI-HOST (Red/Pale/Black)
- -> memory/ops/INDEX.md      Windows ops: reboot recovery runbook, portal lifecycle, ground-truth checks, probe scripts

## Global files (shared by all folders)
- -> agent_portal.py          server :8099; /api/chat, /api/memory, /api/file(+raw); THIS file's first 1600 chars go into every group prompt
- -> agents.json              agent profiles: model_id alias, temperature, reasoning, tools[], max_tool_calls
- -> index.html               frontend: Solo/Group, cross-talk loop, ■ Stop, ↺ Reset; HARD-REFRESH after edits
- -> DESIGN.md                design-system doc (6.1 KB); visual language + component tokens — NOT a behavior spec
- -> MEMORY.md                HOT FILE ONLY (state line + counter + recent notes); keep it small
- -> TODO.md                  work plan, newest section at top
```
Delta vs current: portal sub-index description expanded (was "bugs + architecture" only); DESIGN.md added to Global files (closes v1-inventory flag 3).
r6 correction (2026-11-12): FILE ACCESS block restored to exact live injected-map wording — r5 draft had dropped the bullet-2 example and all of bullet 3, a regression if applied as-is.

## 2. memory/portal/INDEX.md — add one pointer line
`- -> merge-pack.md    curation-ready patch for White: target root index + DESIGN.md entry (r5)`

## 3. file-links cross-ref (DONE on Pale r5)
Cross-reference block already inserted at top of live `memory/portal/file-links.md` (KEEP-BOTH pointer to bundle bugs/file-links-sandbox.md). When White merges, copy that block over — content is identical, no reconcile needed.

## 4. (r7 addendum, 2026-11-13) Per-agent memory module — Archivist
Human directive: each agent keeps a mini memory + TODO alongside the global files. Files exist on Pale at `memory/archivist/MEMORY.md` + `memory/archivist/TODO.md` (shared sandbox folder).
- Copy both into the White tree under `memory/archivist/`.
- Add to root INDEX Sub-indexes: `- -> memory/archivist/   Archivist mini-memory + TODO (per-agent pattern; other agents follow same layout)`
- Independent of steps 1→3; safe to apply alone; no bundle byte-read needed. Other agents' modules land the same way as they appear.

## Explicitly NOT in this pack (gated elsewhere)
- Any of the 15 LISTED merge rows: need White byte-verify first (v1-inventory checklist).
- The 29 UNLISTED rows: need a `dir /s /b` from White to even enumerate (r4 manifest says 44 total; attachment listed 15).
- Canonical single round log on White: still my standing proposal, pending Orchestrator sign-off.

## 5. (r41 addendum, 2026-11-13) Root INDEX pointer for synthesis records [VERIFY]
Scribe finalized the planning-meeting record at `memory/synthesis/2026-11-13-planning-meeting.md` (final addendum: Mechanic no-new-drop, 4-leaf per-host drift checklist, open :8888 flag). NOT on Pale yet (memory/synthesis/ absent in r41 sweep) -> lands with the White drop.
When applying step 1's root index, also add to Sub-indexes:
`- -> memory/synthesis/   dated meeting/planning records (per-date files; newest = 2026-11-13 planning-meeting closeout)`
[VERIFY] byte-check the file exists on White before adding the line. Independent of steps 1-4; safe to apply alone.
