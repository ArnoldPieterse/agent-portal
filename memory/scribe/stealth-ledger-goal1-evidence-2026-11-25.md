# Stealth Ledger — Goal 1 Evidence (2026-11-25)
**Goal:** Daily $ ledger + winner/loser scorecard
**Artifacts:**
- memory/scribe/stealth-ledger.md — schema doc, 3-WF attribution columns, weekly scorecard table
- memory/scribe/stealth-ledger.jsonl — Day-0 baseline entry (all zeros, note: engine launched not yet deployed)

**Verification:**
- [x] File exists at correct path
- [x] Schema defines all required fields (date, outreach_staged, replies, demos, revenue_usd, per-WF breakdown)
- [x] JSONL first line is valid JSON with all schema fields present
- [x] Weekly scorecard table defined with winner/loser columns
- [x] Per-workflow attribution matches Builder's 3 workflows (WF1 AR Followup, WF2 Weekly Report, WF3 Reminder Pipeline)

**Status:** REACHED — structure + Day-0 baseline complete. Daily entries will accumulate as engine goes live.
