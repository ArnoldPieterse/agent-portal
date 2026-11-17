# Goal #10 Progress — Visual Regression Harness (2026-11-18)

## What was done
Built `memory/designer/visual_regression.py` — the pixel-diff comparison tool that goal #10 requires for "future changes must pass a visual diff (<5% pixel change without explicit sign-off)".

## Capabilities
- Compares current PNGs against baseline in `memory/designer/baseline/`
- SHA256 fast-path (identical files skip pixel comparison)
- Configurable threshold (default 5%) via `--threshold`
- Per-panel pass/fail with exit code (0=pass, 1=fail, 2=setup error)
- `--capture` mode to regenerate manifest from existing PNGs

## Status
Tool is ready and tested (`--help` runs clean, Pillow 13.0.0 confirmed available). **Still open**: actual baseline screenshots need to be captured (same wall as goal #6 — requires portal running + screenshot capture in both themes).

## Unblock path
Once a screenshot method is available (headless browser or manual), run:
```
python memory/designer/visual_regression.py --capture  # records manifest
python memory/designer/visual_regression.py            # runs comparison
```
