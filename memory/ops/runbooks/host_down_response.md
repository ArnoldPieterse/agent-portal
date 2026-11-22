

<!-- runbook-lessons:generated -->

## Lessons Learned

### 1. P2 incident detected (2026-11-22T21:25:18)

**What worked:**
- Auto-classification correctly identified host_down on host 'white' as P2 (severity 2).

**What didn't work:**
- Host 'white' went down without prior warning - no early-degradation alert fired before full loss.

**Recommended changes:**
- [ ] Add a pre-failure probe for host 'white': if response latency exceeds 2x baseline for 3 consecutive checks, emit a P3 warning before it escalates to P2 host_down.

### 2. P2 incident detected (2026-11-22T21:25:23)

**What worked:**
- Auto-classification correctly identified host_down on host 'white' as P2 (severity 2).

**What didn't work:**
- Host 'white' went down without prior warning - no early-degradation alert fired before full loss.

**Recommended changes:**
- [ ] Add a pre-failure probe for host 'white': if response latency exceeds 2x baseline for 3 consecutive checks, emit a P3 warning before it escalates to P2 host_down.
