# Research Brief Template (Researcher) v1

Standard output format for ANY research task. Copy this skeleton; fill every field.
The validator (`python memory/researcher/validate_brief.py <brief_file>`) enforces presence
of the required sections and a minimum evidence count.

## Required fields

| # | Field | Format | Rule |
|---|-------|--------|------|
| 1 | **Claim** | one-sentence, falsifiable statement | exactly one; no hedging verbs like "may/seem" in the claim line itself is fine elsewhere |
| 2 | **Evidence** | list of >=3 independent sources | each item: `[n] <source type>: <url or ref>` ; must be distinct sources (no duplicates) |
| 3 | **Confidence** | `High` / `Medium` / `Low` + one-line justification | pick exactly one label; justify with source agreement/corroboration |
| 4 | **Open Questions** | list of unresolved items, or `(none)` | explicit — never leave the section empty/blank |
| 5 | **Follow-up Actions** | list of next steps, or `(none)` | each action nameable + owner-able; explicit if none |

## Skeleton (copy below the `---`)

```
# BRIEF: <short title>
Date: YYYY-MM-DD
Researcher: Researcher
Status: OPEN | CLOSED

## Claim
<one falsifiable sentence>

## Evidence
[1] web_search: <url>
[2] kb: memory/researcher/<file>.md
[3] web_search: <url>

## Confidence
<High|Medium|Low> — <one-line justification>

## Open Questions
- <question or (none)>

## Follow-up Actions
- <action (owner)> or (none)
```

## Validation rules (enforced by validate_brief.py)
1. All 5 section headers present (`## Claim`, `## Evidence`, `## Confidence`, `## Open Questions`, `## Follow-up Actions`).
2. Claim has non-empty content.
3. Evidence lists >=3 distinct numbered sources `[n] ...`.
4. Confidence line contains exactly one of High/Medium/Low (case-insensitive) + a justification after it.
5. Open Questions and Follow-up Actions are non-empty (a `(none)` marker counts as present).

Exit codes: 0 = PASS, 1 = FAIL (reasons printed), 2 = usage/IO error.
