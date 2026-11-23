# Evidence: Goal 2 — Decision Provenance Overlay (REACHED 2026-11-23)

Artifact: `ui/cockpit-provenance.html` (self-contained spec + interactive demo, 14KB)

## Acceptance criteria verification
| # | Criterion | Status | Proof |
|---|-----------|--------|-------|
| 1 | Every primary data point has a provenance hook | ✅ | 3 demo hooks with `data-prov`, `.prov-hook` class, `tabindex="0"`, `role="button"` |
| 2 | Chain renders <= 3 hops deep | ✅ | JS enforces `hops.slice(0, 3)`; structure: agent → evidence → verification |
| 3 | Stale evidence (>7d) flagged in chain | ✅ | `data-stale="true"` triggers orange border + badge; demo data includes stale examples (8d, 9d) |
| 4 | Keyboard-dismissable + SR labeled | ✅ | Escape closes overlay; `role="dialog"`, `aria-label="Decision provenance"`, focus returns to originator |

## Integration contract documented
- API: `/api/provenance/<decision-id>` response shape specified
- Stale threshold configurable via `data-stale-threshold` attribute
- Exposed as `window.provenanceOverlay.{open, close}` for cockpit.js integration
