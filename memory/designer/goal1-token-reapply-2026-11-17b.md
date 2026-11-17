# Goal #1 — Token layer re-applied (2nd pass, 2026-11-17)

Mirror reverted ui/app.css to 23 tokens. Re-applied full layer.

## Changes
- :root expanded 23 → 36 tokens (+13): radius-sm/md/lg, shadow-md, dur-fast/med/pulse/spin, on-accent, flink, link-hover, bg-hover, dim-alt
- 30× border-radius:Npx → var(--radius-*)
- All transition/animation durations → var(--dur-*)
- Semantic color replacements: #fff→--on-accent, #2a3342→--bg-hover, #6db1ff→--flink, #9ccaff→--link-hover, #8b949e/#8b93a7→--dim-alt
- box-shadow → var(--shadow-md)

## Acceptance test (all PASS)
- Raw border-radius px outside :root: 0
- Raw durations in transitions/animations: 0
- Invalid .var() patterns: 0
- Remaining hard-coded hex: 23 occurrences (22 unique) — all component-specific per gap analysis

## Durability
Reapplication script: memory/designer/reapply_tokens.py (idempotent, checks if already applied)

File: ui/app.css (19894 bytes, 235 lines)
