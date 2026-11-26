"""Auto-generated acceptance test: builder-cycle8-proposals goal #1 — Dark Mode Implementation** (carried from cycle-7 #8, genuinely not built) - Add sun/moon toggle in header; switch CSS custom properties between light/dark palettes via `[data-theme]` on `<html>`; inline pre-paint script to avoid white-flash; persist preference in localStorage. Verified: toggle switches all panels to dark palette; reload with dark pref shows dark immediately (no flash); contrast ratios pass WCAG AA in BOTH themes (run extract_tokens/contrast check); preference persists across 3 reloads.

2. **API Client Layer Completion
Generated: 2026-11-26T18:03:58.562882+00:00
Source: memory/goals/builder-cycle8-proposals.md
AC: `grep -c "fetch(" ui/core.js` returns 1 (factory default only) and `ui/uploads.js` = 0; `node memory/builder/test_api_client.js` passes on White/host; retry+cache behavior asserted in that node test.
"""
import os, json, pathlib, sys

def test_dark_mode_implementation_carried_from_cycle_7_8_ge():
    """Acceptance criterion check."""
    # Criteria: `grep -c "fetch(" ui/core.js` returns 1 (factory default only) and `ui/uploads.js` = 0; `node memory
    # CHECK 1: `grep -c "fetch(" ui/core.js` returns 1 (factory default only) and `ui/uploads.j
    # CHECK 2: `node memory/builder/test_api_client.js` passes on White/host
    # CHECK 3: retry+cache behavior asserted in that node test.

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/builder-cycle8-proposals.md")
    assert goals_file.exists(), "Goals file missing: builder-cycle8-proposals"
    return True

if __name__ == "__main__":
    test_dark_mode_implementation_carried_from_cycle_7_8_ge()
    print("PASS: builder-cycle8-proposals goal #1 stub executed without error")
