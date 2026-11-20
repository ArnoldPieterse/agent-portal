# Builder - 10 goals (set 2026-11-20, cycle-8)

Focus: Portal production readiness + build pipeline completion. Cycle-7 integrated the component library and API client; cycle-8 finishes the remaining wiring, adds resilience, and makes deployment one-command.

1. **Build-Verify-Pin --apply (host seat)** - Execute `python memory/builder/build_verify_pin.py index.html --apply` from a non-sandbox White seat where memory_mirror.py is present (non-zero). Verified: PIN_FILES in memory_mirror.py updated with new sha12; canonical backup file created; git commit made; portal serves updated file without revert. (pointer: memory/builder/apply_a4_a5_r35.py)

2. **Complete API Client Wrappers** - Wrap the remaining 6 raw fetch() calls in core.js (fleetStatus, getFile, postChatStream, runEventsStream, fleetDepsGraph + any others) with typed apiClient methods. Target: zero direct fetch() calls in ui/*.js except the apiClient internal implementation. Verified: grep "fetch(" in ui/core.js + ui/uploads.js returns only api-client.js hits; all 17 endpoints have typed wrappers; node --check passes. (verified: 2026-11-20 - Goal 2 (Complete API Client Wrappers) DONE: Added 10 new typed wrappers to ui/api-client.js (listModels, listKnowledgeBases, listTools, getMemory, getRunState, postRunStop, getActivity, fleetVramAlert)

3. **Portal Error Boundary** - Add a global error boundary to core.js: wrap all API calls in try/catch, display user-friendly error messages (not raw JSON), add retry button for transient errors (408/500/503). Verified: simulated 500 shows friendly message + retry; network disconnect shows offline banner; no unhandled promise rejections in console. (pointer: memory/builder/error_boundary_increment3-2026-11-20.md)

4. **Component Library v2** - Add 3 new components to ui/components.js: Modal (overlay + close on ESC), Toast (auto-dismiss notification, top-right), LoadingSpinner (skeleton screen for async panels). Verified: all 3 render correctly; Modal traps focus; Toast auto-dismisses after 4s; Spinner shows during simulated 2s delay; node --check passes. (pointer: memory/builder/component_refactor_regression_2026-11-20.md)

5. **Upload Pipeline Hardening** - Add to uploads.js: file type validation (allow: .md, .json, .txt, .py, .js, .css, .html; block executables), size limit (10MB), progress bar during upload, error message on rejection. Verified: .exe upload rejected with clear message; 11MB file rejected; progress bar visible during upload; valid .md file uploads successfully.

6. **Fleet Status Panel** - Build the fleet tab UI: per-host VRAM bar (green<70%, amber 70-85%, red>85%), agent cards showing model alias + status (active/idle/wedged), trend sparkline for 24h usage. Data from /api/fleet/status. Verified: all 4 hosts render; VRAM bars reflect actual values; agent cards show correct status; no JS errors with 8 agents. (pointer: memory/builder/designer-goal2-fleet-states-2026-11-18.md)

7. **Dark Mode Theme** - Implement light/dark theme toggle using CSS custom properties (design tokens already in app.css). Toggle button in header; preference persisted in localStorage. Verified: both themes render without contrast violations; toggle switches all colors; refresh preserves preference; WCAG AA contrast maintained in both modes. (pointer: memory/builder/verify_theme_toggle_2026-11-17.md)

8. **Portal Performance Optimization** - Lazy-load non-visible panels (only fetch data when panel first opened); debounce API polling to max 1 request/endpoint/30s; add loading states for async content. Verified: initial page load <2s (measured via performance.now()); no duplicate requests within 30s window; all panels show spinner during load.

9. **UI Module Test Suite** - Create memory/builder/ui-tests/: node-based smoke tests that verify each ui/ module loads without error, exports expected functions, and handles edge cases (null data, empty arrays, oversized strings). Run via `node memory/builder/ui-tests/run.js`. Verified: all 5 test files pass; a deliberate break in core.js is caught; run time <10s.

10. **One-Command Deploy** - `python memory/builder/deploy.py [file]`: validates syntax, runs UI tests, syncs to portal root, advances pin if needed, git commits + tags. If no file arg, deploys all changed files. Verified: running on a modified ui/ file completes all steps; a syntax error halts with clear message; git tag created; portal serves updated content.
