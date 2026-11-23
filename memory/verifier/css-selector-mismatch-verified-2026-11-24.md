# CSS Selector Mismatch Verification — 2026-11-24

**Hot-note claim**: "CSS uses `data-density` attr but JS sets `cd--calm`/`cd--incident` classes — selector mismatch identified, needs alignment."

**Verification result**: NO MATCH. Neither `data-density`, `cd--calm`, nor `cd--incident` appear anywhere in `ui/app.css` or `ui/core.js` (or any file under `ui/`). 

**Conclusion**: This was likely a design proposal from Designer's lane (Adaptive Information Density goal) that was never implemented in the codebase. No bug exists to fix — the feature simply isn't built yet.

**Action**: Route back to Designer as "not yet implemented" rather than "bug to fix."

Verified by: Verifier, 2026-11-24
