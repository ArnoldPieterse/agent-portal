# Context Handoff Template

Standard format for passing context between agents.

## Format

```markdown
# HANDOFF: <task_title>

**From:** <agent_name>
**To:** <agent_name>
**Date:** YYYY-MM-DD

## Task
<one-line description of what needs to be done>

## Completed Steps
- <step 1 already done>
- <step 2 already done>

## Current State
<where things stand right now; what works, what doesn't>

## Blockers
- <blocker 1> (or "none")

## Next Action
<the single most important next step, with owner if different from recipient>

## Relevant Files
- `path/to/file1` — what it contains
- `path/to/file2` — what it contains
```

## Validation Rules
1. All 6 sections present: Task, Completed Steps, Current State, Blockers, Next Action, Relevant Files
2. From/To fields non-empty and are valid agent names
3. Date is valid YYYY-MM-DD
4. At least one completed step OR task explicitly marked as new (no prior work)
5. Relevant Files paths must be relative (no drive letters, no absolute paths)
6. Next Action is a single sentence or bullet (not multi-paragraph)
