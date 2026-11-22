

<!-- runbook-lessons:generated -->

## Lessons Learned

### 1. failure (STUDIO_TIMEOUT_EXCEEDED) (2026-11-17 00:41:09)

**What didn't work:**
- Studio on host 'UnknownHost' exceeded 300s timeout during boot recovery - service did not come up.

**Recommended changes:**
- [ ] Increase boot timeout from 300s to 450s for hosts with large model loads, or add a staged readiness check (port open -> model loaded -> first inference OK).

### 2. failure (STUDIO_TIMEOUT_EXCEEDED) (2026-11-17 00:41:12)

**What didn't work:**
- Studio on host 'UnknownHost' exceeded 300s timeout during boot recovery - service did not come up.

**Recommended changes:**
- [ ] Increase boot timeout from 300s to 450s for hosts with large model loads, or add a staged readiness check (port open -> model loaded -> first inference OK).
