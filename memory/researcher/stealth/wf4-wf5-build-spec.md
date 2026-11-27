# WF4 / WF5 Build-Readiness Spec (Researcher assist to Builder)
Created: 2026-11-26 | Extends task-inventory.md gap analysis. Purpose: give Builder exact
input->output contracts + data sources so WF4/WF5 can be packaged WITHOUT re-research.
Source basis: task-inventory.md rows #4 (CRM updates) + #5 (lead follow-up), both HIGH feasibility,
adjoining existing WF3 reminder logic. Revenue model from task-inventory alignment table.

## WF4 — CRM Record Updates & Enrichment (task #4)
Pain: stale/missing fields across contacts+deals; data-entry labour $35-60/hr AUD.
### Input -> Output contract
- INPUT: source-of-truth trigger event (new enquiry form / email parse / webhook) + existing record id.
- OUTPUT: enriched record diff (fields added/corrected) + confidence score per field + audit log line (jsonl).
- Fields to auto-fill (priority order): full_name, email, phone, company, industry, role, source_channel, last_touch_ts.
### Data sources (for enrichment lookups)
1. Inbound form payload (primary — no external call).
2. Email header parse (From/Reply-To -> name+email; domain -> company guess).
3. Company-domain -> industry heuristic table (small local map; NO paid API to keep demo self-contained).
4. Optional: free enrichment endpoint stubbed behind a `--live` flag (default OFF so WF runs air-gapped in demo).
### Automation approach
- Event-triggered (not batch): on new lead, run enrich() -> merge into record if confidence>=0.7, else queue for human review.
- Idempotent: key on (email normalized); re-run is a no-op if fields unchanged.
- Human-in-loop ONLY for low-confidence or conflicting-source fields (keeps "exceptions to human" pattern from bookkeeping WF).
### Edge cases
- Duplicate email (case/typo) -> fuzzy match threshold 0.85, flag merge, never auto-delete.
- Missing domain / personal mailbox -> industry=UNKNOWN, do not block record creation.
- Conflict: form says company X, domain says Y -> keep form value (user-entered wins), log conflict.
### Demo dataset spec
- 20 synthetic leads: 5 dupes (case/typo variants), 3 missing-domain, 2 source-conflicts, rest clean.
- Pass criterion: 18/20 auto-enriched >=0.7 conf; 2 correctly routed to review; 0 data loss on re-run.
### Revenue model
$350-800/client/mo (data-hygiene retainer) — higher margin than WF1, sell as add-on to WF3.

## WF5 — Lead Follow-up Scheduling & Chasing (task #5)
Pain: leads go cold; sales-admin labour $40-70/hr AUD chasing manually.
### Input -> Output contract
- INPUT: lead record + stage (new/contacted/proposal) + response state (replied / no-response N days).
- OUTPUT: scheduled follow-up action (channel, copy variant, send-at ts) + escalation decision (bump to human / close / re-engage).
### Automation approach
- Reuse WF3 reminder engine scheduling core; add a stage-aware cadence table:
  - new -> contact at +1d, +3d, +7d (email primary, SMS optional)
  - contacted-no-reply -> +4d, +10d, then human-touch flag
  - proposal -> +2d, +5d; after +10d no-reply -> soft-close + re-engage at +30d
- Stop-on-reply: any inbound reply resets timer and flips state (this is the key differentiator vs blind WF3 reminders).
### Edge cases
- Reply detection false-positive (autoresponder/ooo) -> regex filter list, do NOT reset on OOO.
- Opt-out / unsubscribe -> hard-stop all sends, mark record, never re-add.
- Cross-channel spam guard: max 3 touches per lead per 14d regardless of stage.
### Demo dataset spec
- 15 synthetic leads across the 3 stages; 2 with OOO replies, 1 opt-out, rest clean.
- Pass criterion: cadence table fires on schedule (dry-run clock), reply resets timer for 10/10 real replies,
  OOO ignored (2), opt-out hard-stops (1), spam-guard caps touches at 3 (verified).
### Revenue model
$250-600/client/mo; highest perceived ROI of the two (direct pipeline impact) — lead with this in sales demo.

## Builder integration notes
- Both reuse WF3's scheduler + channel abstraction -> lowest build cost of remaining tasks.
- Suggest order: WF5 first (highest demo impact, reuses most), then WF4 (data-hygiene add-on).
- Keep external enrichment OFF by default so demos run air-gapped (matches WF1-3 pattern in run_stealth_jobs.py).

## Verification (this spec deliverable)
- [x] WF4 + WF5 each: input->output contract, data sources, automation approach, edge cases, demo dataset spec, revenue model.
- [x] Builds on task-inventory.md #4/#5; no new research required — Builder can package from this directly.
