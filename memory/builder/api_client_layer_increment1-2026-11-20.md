# Goal #2 API Client Layer - increment 1 (2026-11-20)

Built ui/api-client.js (150 lines, <500 rule): DI pure core backoffDelay/cacheGet/cacheSet/runWithRetry (exp backoff + full-jitter, maxRetries=3 -> 4 attempts), TTL-30s GET cache, 17 typed wrappers for all /api/* endpoints, ApiError class, UMD export (module.exports + window.apiClient).

GATE (this host, no JS engine): python memory/builder/gate_api_client.py -> PASS (balanced delims, retry core, cache core, 17/17 endpoint strings, UMD/global, <500 lines).

Canonical in-process test authored: memory/builder/test_api_client.js (stubbed fetch; asserts 500->retry attempts=4, 200-after-500s, cache dedup within TTL, non-retried POST single attempt, backoff monotonic+capped). Run: node memory/builder/test_api_client.js -> exit 0.

REMAINING (next step): wire core.js/uploads.js fetch() calls to apiClient; execute node test on a node-capable host. Sandbox has no node runtime (verified).
