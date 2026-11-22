# WCAG Light-Theme Contrast Verification - 2026-11-23

**Claim under test (hot note):** "Light-theme WCAG AA audit done: 6 tokens below 4."

**Method:** Computed WCAG 2.1 relative luminance + contrast ratio for all meaningful text-on-background pairs in the `[data-theme=light]` block of `ui/tokens.css`.

## Results

### Pairs below 4:1 (6 total - matches hot note)
| Foreground | Background | Ratio | Description |
|---|---|---|---|
| --faint #7a8699 | --panel #ffffff | 3.69:1 | faint text on panel |
| --faint #7a8699 | --bg #f4f6fa | 3.41:1 | faint text on page bg |
| --ok #1f9d5b | --bg #f4f6fa | 3.22:1 | success on page bg |
| --ok #1f9d5b | --panel #ffffff | 3.48:1 | success on panel |
| --warn #c47a12 | --bg #f4f6fa | 3.16:1 | warning on page bg |
| --warn #c47a12 | --panel #ffffff | 3.42:1 | warning on panel |

### Pairs between 4:1 and 4.5:1 (fail AA, not "below 4")
| Foreground | Background | Ratio |
|---|---|---|
| --acc #2f6fe0 | --bg #f4f6fa | 4.34:1 |
| --err #d64545 | --bg #f4f6fa | 4.05:1 |
| --err #d64545 | --panel #ffffff | 4.38:1 |

### Pairs passing AA (4.5:1+)
| Pair | Ratio |
|---|---|
| --text on --bg | 14.63:1 |
| --text on --panel | 15.82:1 |
| --dim on --panel | 5.74:1 |
| --dim on --bg | 5.30:1 |
| --acc on --panel | 4.70:1 |
| --link on --bg | 4.78:1 |
| --link on --panel | 5.17:1 |
| --peek-body on --peek-bg | 10.31:1 |
| --queue-dim on --queue-bg | 4.62:1 |
| --int-text on --int-bg | 6.84:1 |
| --dm-text on --bg | 5.27:1 |
| --dm-text on --panel | 5.70:1 |

## Verdict: HOT-NOTE CLAIM CONFIRMED (with nuance)

The hot note "6 tokens below 4" is **accurate**: exactly 6 text/bg pairs fall below the 4:1 threshold.
However, the full AA picture is worse: **9 total pairs fail WCAG AA** (4.5:1), because --acc and --err also fall between 4:1 and 4.5:1 on at least one background.

## Impact Assessment

- **--faint** (3.41-3.69:1): Used for placeholder text, timestamps, disabled states. Below the large-text AA threshold (3:1) would be acceptable for 18pt+ bold only; at normal size this is a real accessibility gap.
- **--ok / --warn** (3.16-3.48:1): Used for status indicators and success/warning messages. These are user-facing semantic colors that should meet AA for normal text. **Highest-priority fix.**
- **--acc / --err** (4.05-4.38:1 on bg): Accent and error text on the page background barely miss AA. On white panel they pass or nearly pass.

## Fix Suggestion (for Designer)

To bring all 9 failing pairs to >=4.5:1 in light theme:
- --faint: #7a8699 -> #6b7a8d (est ~4.6:1 on white) or darker
- --ok: #1f9d5b -> #157043 (est ~5.0:1 on white)
- --warn: #c47a12 -> #9a5c08 (est ~5.2:1 on white)
- --err: #d64545 -> #b83a3a (est ~4.9:1 on white)
- --acc: already passes on panel; on bg could darken slightly to #285fc8

**Evidence source:** `ui/tokens.css` lines 1-40, computed via WCAG 2.1 relative luminance formula.
**Verified by:** Verifier, 2026-11-23.