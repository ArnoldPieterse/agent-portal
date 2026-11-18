# Goal #2 Padding Audit (Mechanic assist, 2026-11-19)

Scanned `ui/app.css` for hardcoded px padding/margin values not using var().

**Result: 5 lines remain** (all minor structural values):

| Line | Selector | Value |
|------|----------|-------|
| 1 | `.checks input` | margin:0 |
| 2 | `.mh-v` | margin:2px 0 |
| 3 | `h1` | margin:0 0 4px |
| 4 | `.ft-models` | padding-left:16px |
| 5 | `.fhs-overall` | padding:2px 6px |

All are ≤16px and serve structural spacing (not density-reducing whitespace).
Recommendation: tokenize as `--sp-0`, `--sp-1`(2px), `--sp-1.5`(4px), `--sp-3`(6px), `--sp-4`(16px) if full tokenization is the acceptance bar.
The density-reducing large paddings (16px+ vertical on panels) are already tokenized per PROGRESS note.

Artifact: this file. Owner: Designer. Assist: Mechanic.