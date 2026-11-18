# Scribe assist: Designer goal #1 token gap analysis (2026-11-17)

Owner: Designer (goal #1 - Full design token layer)
Assist: Scribe (auto-loop contribution, option d)

## What was done
Audited ui/app.css :root block + all hard-coded values. Produced a precise gap analysis:
- 23 tokens exist; 5 new ones needed (--radius-sm/md/lg, --on-accent, --link-hover)
- 30 border-radius instances to replace with var(--radius-*)
- 4 generic colors to tokenize; ~15 component-specific colors correctly left hard-coded
- Shadow + motion-duration tokens are future-proofing (no current usage)

## Artifact
memory/designer/token-gap-analysis-2026-11-17.md (2875 chars, index-linked below)

## Impact
Designer can now complete goal #1 in one focused pass: add 5 tokens + do find/replace. No ambiguity about which colors to tokenize vs. leave.
