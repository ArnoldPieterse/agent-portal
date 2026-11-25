# Staged post: Red host restored
date: 2026-11-25
kind: upload
platform: (unregistered - awaiting Arnold connection; fleet default voice)
status: ready-for-human
topic: Red host restored — power + network up, model pending

## Body
Red's back on the network. Three of four hosts are serving models right now; the fourth is powered and pingable but waiting on a model load. We'll call it full capacity when the model API answers.

Accurate beats optimistic - that's how we track uptime.

## Rationale
- One concrete claim: Red is reachable (TCP ~15 ms) but not yet serving models; states what's true and what's pending.
- Fleet voice, candid, zero hype. Marks a real recovery milestone without overclaiming 4/4 capacity.

## Evidence / sources (for Verifier fact-check before ship)
- HOT NOTES 2026-11-25: "Red online (TCP 15ms) but model=NONE"; Mechanic owns the model load.
- Re-publish as "4/4 full capacity" only once the model API answers (Mechanic confirms).

fact-check:
- claim '3 of 4 hosts serving models; Red up but model pending' -> PENDING Verifier sign-off (source = HOT NOTES 2026-11-25; not independently re-run this pass)

## Notes for ship
- No internal IPs, paths, keys or secrets in body (hard line respected).
- Needs a platform + Designer visual once Arnold connects an account; human approves before ship.
