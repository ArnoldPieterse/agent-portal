# Goal #8 Alert Triage View — Evidence

Date: 2026-11-23
Files: ui/alert-triage.js (7554B, 203 lines) + ui/alert-triage.css (3237B, 142 lines)

## Verification (12/12 selfTest pass)
- sortAlerts: P1 before P3, same-severity newer first ✓
- Empty/null handling ✓
- SEVERITY_ORDER monotonic ✓
- STATUS_LABELS complete (new/acknowledged/resolved) ✓
- XSS escaping ✓
- Mixed severity ordering ✓

## Acceptance criteria
- [x] alerts sort correctly (P1 newest first) — sortAlerts with SEVERITY_ORDER + detected_at
- [x] acknowledge button updates state — optimistic local update + POST /api/alerts/:id/ack
- [x] resolved alerts move to collapsed "resolved" section — <details class="at-resolved">
- [x] empty state is clean — checkmark icon + "No active alerts. Fleet is nominal."

## Design decisions
- Severity left-border (4px) + badge for at-a-glance triage
- Ack button: compact 11px, hover fills with accent, touch-target >=36px on mobile
- Resolved section uses native <details> (zero-JS expand/collapse)
- Polling at 15s (slower than topology's 10s since alerts are less time-critical)
- CSS uses portal tokens (--err/--warn/--acc/--ok) for consistency with cockpit theme
