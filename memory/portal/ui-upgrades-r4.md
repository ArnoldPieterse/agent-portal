# ui-upgrades-r4 — Designer UI spec (persisted 2026-11-13)

Status: DESIGN DECISIONS, persisted from r4 in-chat canvas (was "not yet a file" per v1-inventory round-4 delta). Scope = `index.html` only; all changes hard-refresh-safe. Token values re-derived from DESIGN.md at build time — this module records decisions, not pixels.

## The four upgrades
1. **Per-agent identity** — stable color + monogram per agent in Group view. Color is never the sole differentiator (WCAG 1.4.1 use-of-color); monogram carries the identity, color reinforces. Palette must stay readable on existing Solo/Group background; contrast ≥ 4.5:1 for text tokens.
2. **■ Stop** — stream-only semantics; arm-then-confirm pattern (first click arms, second click within window stops) so an accidental tap can't kill a generation mid-flight. Armed state needs a visible affordance (label change or badge), not color alone.
3. **↺ Reset** — arm-then-confirm with ≤3s arming window; same visibility rules as Stop. Both controls share one armed-state visual language.
4. **File links → relative-path chips** — see `memory/portal/file-links.md` (Archivist DRAFT, scope locked in round-table). My render-time rules there: absolute/drive-letter paths get a flagged NON-clickable chip with warning badge (not color alone); traversal/nonexistent paths show explicit "not found" state naming the offending path. Cross-ref only — do not duplicate spec content here.

## Build-queue position (my recommendation, planning meeting 2026-11-13)
- Increment 1 = items 1–3 + chip rendering WITHOUT `/api/manifest` (flag-only + direct `/api/file?raw`). Rationale: manifest was parked by Builder 2026-11-11 and Quinn's finding says no authorship metadata exists, so the manifest adds nothing to verification; shipping it later is additive, not rework.
- Fleet Status panel (`memory/portal/fleet-status.md`) queues behind two spec sentences: idle/busy definition in the decision line (testability) + Orchestrator's one-sentence spec before Builder cuts the stub. My constraints already recorded there: compact 4-row table in header/sidebar of existing layout (no new top-level view), loading/error/empty states, keyboard-reachable, visible last-updated timestamp, `unknown` = first-class stale state never rendered green/idle.

## Acceptance criteria — increment 1 (written pre-change, per Verifier's gate rule)
Measurable pass criteria; Verifier adjudicates from these, not from vibes. Shared constant: `NAMED_ARM_MS = 3000` (one named constant for Stop and Reset arming windows; no magic numbers in markup).
- **AC-1 Identity** — fixed mapping table (alias → monogram + color hex) committed with the change; every Group-view agent card renders its monogram + `data-agent="<alias>"`; no two agents share a monogram; text contrast ≥ 4.5:1 on current background; removing color still leaves cards distinguishable by monogram (WCAG 1.4.1). Pass = DOM snapshot of a Group thread with ≥3 agents shows distinct monograms per alias.
- **AC-2 ■ Stop** — visible ONLY while a stream is active (absent at idle); click 1 arms → visible affordance change (label/badge, e.g. "■ confirm stop"), not color alone; stream keeps running armed; click 2 within `NAMED_ARM_MS` stops the stream and removes the control; arm window expiry returns to unarmed state. Pass = scripted sequence: start generation → 1 click → assert armed class + stream alive → 2nd click → assert stream ended; negative: single click, wait >3s → assert unarmed.
- **AC-3 ↺ Reset** — same arm-confirm pattern, same named constant, shared armed-state visual language with Stop; on confirm the conversation clears to the documented empty state (no orphan messages, no partial DOM). Pass = scripted sequence + post-state DOM assertion (message count 0, input enabled).
- **AC-4 Chips** — fixture list `{relative-ok, Z:\abs, ../traversal, missing}` renders: relative → clickable chip resolving via `/api/file?raw`; drive-letter/absolute → NON-clickable flagged chip with warning badge (text/icon, not color alone); traversal/nonexistent → explicit "not found" state naming the offending path. Pass = pre-change baseline capture of this fixture on White (loopback :8099 policy-blocked from sandboxes, WinError 10013) + post-change capture; diff shows only intended deltas.
- **AC-5 No new endpoints** — increment 1 calls only existing routes; network log of a full session shows no `/api/manifest` or any other unimplemented route. Manifest stays additive, queued later (decision above).

## Gated items (not buildable from Pale)
- Any `index.html` edit lands via Builder on the live tree + White merge path (v1-inventory row 5: MERGE, hard-refresh note required); baseline failing fixture (pre-change curl of relative vs drive-letter path) must be captured where :8099 answers — loopback is policy-blocked from sandboxes (WinError 10013), so that's a White-side or human step.

## Apply-round status (Designer, 2026-11-13 auto-continue r3)
- Reference `ws-b-increment1/index.html` re-verified byte-intact from Pale seat: **sha256-12 = b82dd3b77f4e** (== record); IDENTITY table 8 agents, monograms O/R/B/V/A/S/M/D all unique; worst white-on-token contrast 5.13:1 (verifier) ≥ 4.5; single `NAMED_ARM_MS = 3000` def (6 refs); zero `/api/manifest` calls. AC-1…AC-5 self-checks green.
- Increment-2 mock hash of record (first logged): `designer/increment2-portal-mock.html` sha256-12 = **b4ede3daf6df**.
- Seat constraint re-proven first-hand from Pale: loopback :8099 = WinError 10013; LAN http://192.168.1.179:8099 = timeout (egress policy-blocked). Designer lane therefore CANNOT port or verify live index.html — Inc-1 MERGE remains Builder's, AC adjudication Verifier's.

## Cross-refs
- -> file-links.md    chip + side-panel spec (DRAFT; manifest question open)
- -> fleet-status.md  panel decision/spec (PROPOSED; idle/busy + spec sentence open)
- -> v1-inventory.md   merge rows 3 (DESIGN.md index) + 5 (index.html MERGE)
- -> fleet-status.md   idle/busy PROPOSED definition + one-sentence stub spec added by Designer 2026-11-13 (planning meeting r2), pending Orchestrator/Scribe ratification
