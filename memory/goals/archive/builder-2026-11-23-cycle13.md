# Builder - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes the build layer production-ready: deployable, testable, and maintainable without heroics.

1. **Deployment Script** - `python memory/builder/deploy.py`: a single command that deploys the portal to a fresh host: install deps, copy files, configure env, start service, run smoke test. Verified: runs on a clean directory; portal is serving within 60s; smoke test passes; --undeploy reverses cleanly.

2. **Build Lint Gate** - `python memory/builder/build_lint.py`: before any file change is committed, run: (a) Python syntax check on all .py files, (b) JSON validity on all .json files, (c) no files >50KB in ui/, (d) no TODO/FIXME/HACK comments in production code. Emit pass/fail report. Verified: >=4 checks defined; a syntax error is caught before commit; a 60KB CSS file is flagged; clean codebase passes all checks.

3. **Dependency Manifest** - Create memory/builder/requirements.txt (Python deps) + memory/builder/package.json (Node deps, if any) with exact pinned versions; verify `pip install -r requirements.txt` reproduces the working environment. Verified: manifest exists; fresh venv + install produces a working portal; no "works on my machine" deps (all pinned to exact version).

4. **Error Recovery Patterns** - Document and implement 5 error recovery patterns in the codebase: retry with backoff, circuit breaker, graceful degradation, dead letter queue, and safe restart. Each pattern gets a unit test. Emit memory/builder/recovery-patterns.md + test file. Verified: 5 patterns documented; each has a passing unit test; a simulated failure triggers the correct recovery path.

5. **Code Complexity Gate** - `python memory/builder/complexity_gate.py`: compute cyclomatic complexity for all Python files in the fleet; flag any function with complexity >15 or any file with avg complexity >8. Emit report to memory/builder/complexity-<date>.md. Verified: >=20 files analyzed; a deliberately complex function (nested loops + conditionals) is flagged; report includes suggested refactoring hints.

6. **Feature Flag System** - Implement a simple feature flag mechanism in the portal: flags stored in memory/builder/flags.json; code checks flags before enabling features; --list shows all flags + state; --toggle <name> flips a flag. Verified: 3 features behind flags; toggling a flag changes behavior immediately (no restart); flags persist across restarts.

7. **Build Reproducibility Test** - `python memory/builder/repro_test.py`: from a clean checkout, run the full build process and verify: (a) output is byte-identical to the last known-good build, (b) no non-deterministic artifacts (timestamps in code, random seeds), (c) total build time <120s. Verified: 2 consecutive builds produce identical output; a deliberate timestamp injection is caught; build completes in time.

8. **API Contract Tests** - `python memory/builder/api_contracts.py`: for each portal API endpoint, define its contract (method, path, request schema, response schema, status codes); auto-test against the live endpoint. Emit contract test results. Verified: >=5 endpoints have contracts; a response missing a required field is flagged; a wrong status code is caught; all passing contracts show green.

9. **Hot-Reload Dev Mode** - Implement --dev flag for the portal: watches file changes, auto-restarts on .py change, live-reloads CSS/JS in browser (via WebSocket). Verified: editing app.css triggers browser reload without manual refresh; editing a .py file restarts the server within 5s; --dev not available in production mode.

10. **Build Artifact Registry** - `python memory/builder/artifact_registry.py`: maintain a registry of all build artifacts (scripts, configs, UI bundles): {path, sha256, last_modified, owner, description}. Emit memory/builder/registry.json. Verified: >=30 artifacts registered; each has a valid sha256; a modified file is detected as "changed" on next scan; --verify re-checks all hashes.
