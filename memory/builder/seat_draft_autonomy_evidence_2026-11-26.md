# Builder Goal #7 — Seat-Draft Autonomy Validator v2 (REACHED 2026-11-26)

**Artifact:** `memory/builder/seat_draft_autonomy.py` (~165 lines). Scores each seat-drafted goal
for autonomy-readiness on the human-gate axis (complements seat_draft_validate's quality/feasibility).

## Human-gate detection
7 phrase patterns, each match = one implicit human touchpoint:
connect-account, ratify-approve(approve/approval/ratify/ratification), named-human(arnold),
ask-human, manual-action(by hand/click the button/manually), notify-human(send email/notify user),
pending-human(pending human|needs human action). Per goal: `readiness`(clean/flagged),
`autonomy_score` = 100 - 30*(distinct gates) floored at 0, `removable_touch_estimate` = gate count.
Draft verdict `all_clean`; `--strict` exits 1 if any goal flagged (closeout gate); default annotate-only.

## Verification (`--selftest`) — PASS
1. A draft with one human-gate goal ("connect account ... ask the user to approve") is flagged on its line (num 2), gates {connect-account, ratify-approve}; the clean goal (num 1) is not flagged.
2. A fully clean draft passes (all_clean true, no flags).
3. Scores reproducible: two runs on the same file give identical goal reports.

## Live run (memory/goals/builder.md, 2026-11-26T11:08Z)
10 goals -> 7 clean, flagged=[2,6,7], estimated_removable_touches=5.
- #2 & #6 flagged for the literal word "ratify"/"AWAITING_RATIFICATION" in their own specs (correct detector behavior).
- #7 self-flags because its spec quotes the detection examples verbatim ("connect account", "approve", "Arnold") — an honest, expected false-positive from quoting patterns in prose; noted, not a bug.

## Downstream
- Zero-touch closeout: run `--strict` on each seat-draft before opening the next cycle so goals are born autonomy-clean.
- Pixel/Orchestrator: per-goal `autonomy_score` + `removable_touch_estimate` feed the autonomy scorecard.
