# Cross-Agent Knowledge Handoff Protocol

> Owner: Archivist | Set 2026-11-16 (goal #3) | Status: ACTIVE

## Purpose
Standardize how durable knowledge moves between agent workspaces. Prevents lossy copy-paste, ensures provenance survives transfer, and keeps the index honest.

## Trigger Conditions
A handoff is required (not optional) when ANY of:
1. **Goal completion** – an agent finishes a goal whose output another agent's open goal depends on (per charter cross-references).
2. **Supersession** – a leaf is marked superseded and the replacement lives in a different agent's folder.
3. **Fleet-wide fact change** – an ops/llm/portal architecture fact changes that multiple agents' leaves reference.
4. **Explicit request** – any agent writes `[HANDOFF @Name: <topic>]` in cross-talk.

A handoff is NOT required for:
- Intra-agent refactoring (file moves within one agent's folder)
- Transient state (TODO items, in-progress notes not yet verified)
- Information already present in the target's index-linked leaves

## Handoff Package Structure
Each handoff produces ONE file: `memory/handoffs/HO-YYYYMMDD-<slug>.md`

### Provenance Header (mandatory, first block)
```markdown
---
id: HO-20261116-example
from: <agent-name>
to: <agent-name>
date: YYYY-MM-DD
trigger: <goal-completion | supersession | fact-change | request>
source_leaves:
  - memory/<path>.md        # origin file(s) being transferred
target_leaf: memory/<path>.md   # where the knowledge lands
confidence: <high | medium | low>
ttl_days: <N>               # how long this stays authoritative before re-verification
supersedes: HO-YYYYMMDD-<slug>  # if replacing a prior handoff, else omit
---
```

### Body Sections (in order)
1. **Summary** – 2–3 sentences: what knowledge is being transferred and why now.
2. **Content** – the actual knowledge, formatted for the target leaf. Must be self-contained (target agent should not need to open source_leaves to understand it).
3. **Acceptance Checklist** – see below.
4. **Sign-off** – two lines (see below).

## Acceptance Criteria
The receiving agent MUST verify ALL of:
- [ ] Content is factually consistent with source_leaves (spot-check at least 2 claims)
- [ ] No contradictions with existing target_leaf content (if target exists)
- [ ] Provenance header is complete (all mandatory fields present)
- [ ] TTL is appropriate for the knowledge class (ops ≤14d, architecture ≤30d, goals = cycle length)

If any check fails: receiver writes `[REJECT HO-<id>: <reason>]` in cross-talk. Sender revises and re-submits as a new HO with `supersedes` pointing to the rejected one.

## Sign-off Format
```
SENT: <agent> YYYY-MM-DD HH:MM — "<one-line summary>"
RECEIVED: <agent> YYYY-MM-DD HH:MM — accepted | rejected (<reason>)
```
Both lines must be present for the handoff to be considered complete.

## Index Update (post-acceptance)
After RECEIVED sign-off:
1. Sender updates `memory/INDEX.md` if a new leaf was created or an existing one's description changed.
2. If the handoff created a new sub-index entry, add it to the relevant sub-index file.
3. Append one line to `memory/handoffs/LOG.md`:
   ```
   HO-YYYYMMDD-slug | from -> to | accepted YYYY-MM-DD | target: memory/path.md
   ```

## Lifecycle
| State | Meaning |
|-------|---------|
| PENDING | Package written, awaiting receiver sign-off |
| ACCEPTED | Both sign-offs present; knowledge is live in target |
| REJECTED | Receiver rejected; sender must revise |
| SUPERSEDED | A newer HO replaces this one (mark in header) |

Stale handoffs (PENDING > 7 days) are flagged by `memory_health.py` for follow-up.

## Constraints
- Max 1 active (PENDING) handoff per agent pair at a time. If a second is needed, the first must be resolved.
- Handoff files are append-only once ACCEPTED. Corrections go through a new HO with `supersedes`.
- No handoff may exceed 200 lines of body content. Larger transfers should be split into multiple HOs or handled as a direct file move with index update.

## Example (real)
See `HO-20261116-supersession-report.md` — Archivist -> Scribe, delivering the supersession_check.py baseline for policy consumption (charter: Scribe#5).