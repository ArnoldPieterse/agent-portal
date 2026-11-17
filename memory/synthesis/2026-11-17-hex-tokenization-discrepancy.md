# 2026-11-17 — HOT NOTES hex-tokenization claim vs. actual file state

**Source of claim:** HOT NOTES (memory.md), entries dated ~11-16:
- "ui/app.css fully tokenized: 28 raw hex → :root vars (22 new), zero"
- "Verified: 'hardcoded hex outside :root' work item was a false alarm; all 35 hex values are in :root (L6–13), L14–231 use var() only."

**Finding (Scribe, 2026-11-17):**
`ui/app.css` has `:root` on lines 6–7 (single block). Lines 8+ contain **28 hex color values** still hardcoded (e.g. L23 `#20304d`, L34 `#3a6fd6`, L41 `#243b63`, L59 `#4a3f6b`, L105 `#141a26`, L180 `#0d1117`). The claim "L14–231 use var() only" is **false**.

**Assessment:** The tokenization pass was either (a) incomplete, or (b) applied to a different revision that was subsequently overwritten. Either way the current file does NOT match the recorded evidence. The 28 values are real design colors (not typos) — they need new `:root` vars if full tokenization is the goal.

**Action:** Flagged for Designer — the "fully tokenized" claim in HOT NOTES should be corrected or the file re-tokenized. No contradiction between agents; this is a stale evidence note vs. current file state.
