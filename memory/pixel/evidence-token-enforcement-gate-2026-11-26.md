# Pixel Goal #8 Evidence — High-contrast / token-enforcement audit (2026-11-26)

## Outcome
Zero hardcoded hex color values outside `ui/tokens.css` across the convergence +
fleet JS surfaces, plus a pre-pin grep gate that enforces it.

## Findings
- Scanned 16 files: `ui/cockpit-*.js` (all) + `ui/fleet_*.js`.
- A naive `#[0-9a-fA-F]{3,8}` match yields 5 hits, ALL false positives: HTML numeric
  entities (`&#9888;`, `&#9432;`, `&#8635;` x2) in cockpit-convergence.js and a URL
  fragment in cockpit-forecast.js. A refined detector that excludes '&' -prefixed
  runs (entities) finds **0 real color hex**. Surfaces are already token-clean.
- `ui/tokens.css` present (3837 B): defines design tokens (--acc, --bg, --dim,
  --dot-err, ...) and a high-contrast / forced-colors variant (`prefers-contrast`).

## Deliverable — pre-pin gate
`memory/pixel/prepin_token_gate.py`:
- Detector `(?<!&)#([0-9a-fA-F]{3,8})\b` (negative lookbehind drops HTML entities).
- Default: scans cockpit/fleet JS; exit 0 clean, exit 1 listing file:line violations.
- `--selftest`: proves it rejects an injected color hex and ignores entity/URL forms.

## Verification (both acceptance legs run on this seat)
| Leg | Command | Result |
|-----|---------|--------|
| Rejects injected violation | `python memory/pixel/prepin_token_gate.py --selftest` | SELFTEST PASS — bad->['#ff0000'], ent->[], url->[] |
| 0 violations on current tree | `python memory/pixel/prepin_token_gate.py` | PASS: 0 hardcoded hex colors in 16 cockpit/fleet JS file(s), exit 0 |
| tokens cover high-contrast state | grep tokens.css | prefers-contrast/forced-colors present + token set defined |

## Status: REACHED
