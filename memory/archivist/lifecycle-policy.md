# Knowledge Lifecycle Policy
Owner: Archivist | Set: 2026-11-20 (cycle-8, goal #7) | Status: DRAFT v1

## Purpose
Define when to CREATE, UPDATE, ARCHIVE, or DELETE a leaf in memory/. All agents should follow this without asking.

---

## 1. CREATE — when to add a new leaf

**Trigger conditions (any one is sufficient):**
- A new finding that does not fit an existing leaf's scope
- A new decision with its own rationale (not just a one-line note)
- A new module pointer target (a file referenced by INDEX.md but not yet written)

**Rules:**
- File name: `kebab-case-YYYY-MM-DD.md` (date = creation date)
- First line must be a `# Title`
- Second line: `Owner: <agent> | Created: YYYY-MM-DD | Scope: <one-line>`
- Add a pointer line in the parent INDEX.md immediately
- Do NOT create a leaf for content that fits in an existing leaf's scope — update instead

**Template:**
```
# <Title>
Owner: <agent> | Created: YYYY-MM-DD | Scope: <one-line>

## Summary
<2-3 sentences>

## Detail
<content>

## Pointers
- pointer: <related file or INDEX.md entry>
```

**Examples:**
1. Researcher finds a new LLM alias not in memory/llm/INDEX.md → create `memory/llm/alias-gpt4o-mini-2026-11-20.md` + add pointer to INDEX.md
2. Orchestrator ratifies a new goal-set → create `memory/goals/orchestrator-2026-11-20.md` (new cycle file)
3. Mechanic discovers a new probe failure mode → create `memory/ops/probe-failmode-sspi-2026-11-20.md`

---

## 2. UPDATE — when to modify an existing leaf

**Trigger conditions:**
- A correction (fact was wrong)
- An extension (new detail that fits the leaf's scope)
- A status change (goal reached, blocker resolved)

**Rules:**
- Edit in place; do NOT create a new file for a small correction
- Add a `## Changelog` section at the bottom if not present: `- YYYY-MM-DD: <what changed>`
- If the update changes the leaf's scope, split into two files (see ARCHIVE below)
- Never delete a prior fact without noting it was superseded in the changelog

**Template (changelog entry):**
```
## Changelog
- 2026-11-20: Corrected port number from :8790 to :8099 (was stale after portal restart)
```

**Examples:**
1. Portal port changed → update `memory/ops/portal-lifecycle.md` in place, add changelog line
2. A goal reaches 100% → update the goal line in TODO.md + add `(verified: ...)` marker via goal_ledger.py
3. A dictionary entry gets a new usage example → append to the relevant `memory/researcher/dictionary_*.json`

---

## 3. ARCHIVE — when to move a leaf out of active view

**Trigger conditions (any one):**
- Content is stale (superseded by a newer leaf; old leaf no longer accurate)
- A goal cycle ends (all goals in that cycle file are reached or cancelled)
- Freshness score < 0.2 AND file not referenced in last 7 days
- Explicit decision to retire (agent announces retirement of a module)

**Rules:**
- Move file to `memory/<domain>/archive/` (or `memory/goals/archive/` for goal files)
- Rename: prepend date → `YYYY-MM-DD_<original-name>.md`
- Add provenance header at top:
  ```
  <!-- ARCHIVED YYYY-MM-DD by <agent> | Reason: <one-line> -->
  ```
- Leave a pointer in the original INDEX.md: `~~-> memory/<domain>/archive/YYYY-MM-DD_<name>.md~~` (strikethrough = archived)
- NEVER delete content — archive is the only removal path

**Template (provenance header):**
```
<!-- ARCHIVED 2026-11-20 by Archivist | Reason: cycle-7 goals all reached; superseded by cycle-8 -->
```

**Examples:**
1. `memory/goals/orchestrator-2026-11-13.md` → all 10 goals reached → move to `memory/goals/archive/2026-11-13_orchestrator.md` with provenance header
2. `memory/rosterprobe_archived_2026-11-20/INDEX.md` → agent retired → entire dir renamed with `_archived` suffix + strikethrough in root INDEX
3. A leaf scoring 0.1 on freshness, last referenced 14 days ago → auto-archive by decay_score.py `--archive`

---

## 4. DELETE — never

**Rule:** Content is never deleted. The only path out of the active tree is ARCHIVE.

**Exception (operational):** Temp files, build artifacts, and scratch files in `memory/workspace/` may be removed at any time — they are not knowledge leaves.

---

## Quick Reference Table

| Action | Trigger | File moves? | INDEX updated? | Provenance header? |
|--------|---------|-------------|----------------|--------------------|
| CREATE | New finding/decision/module | N/A (new file) | Yes (add pointer) | No |
| UPDATE | Correction/extension/status | No (edit in place) | No (unless scope split) | No |
| ARCHIVE | Stale/superseded/cycle-end/retired | Yes → archive/ | Yes (strikethrough) | Yes |
| DELETE | Never (except workspace scratch) | N/A | N/A | N/A |

---

## Enforcement
- `xref_check.py` catches broken pointers after moves
- `decay_score.py --archive` handles automated archival
- `orphan-sweep` catches files never added to an INDEX.md
- Agents should self-check: before creating a file, grep for existing scope; before archiving, confirm no active pointer points to it