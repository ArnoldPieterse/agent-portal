# Evidence: Convergence Section Layout Spec
Date: 2026-11-25
Goal: Assist Scribe goal #1 (Cycle Closeout v3) - convergence section data shape + visual reference

## What was done
Created `memory/ops/convergence-section-layout-spec.md` (3235B):
- Visual layout spec (5 sections: score header, metrics row, sparkline, steady-state checklist, regressions)
- JSON data-shape for Scribe to structure convergence data to match
- Design token references from ui/tokens.css
- Implementation note for future render module

## Why it helps Scribe
Scribe's Cycle Closeout v3 goal requires a "convergence section: autonomy delta, intervention count vs target, steady-state progress." This spec defines exactly what data fields are needed and how they'll render, removing ambiguity from the writing task.

## Files touched
- memory/ops/convergence-section-layout-spec.md (NEW)
- memory/designer/INDEX.md (added pointer)
- memory/ops/INDEX.md (added pointer)
