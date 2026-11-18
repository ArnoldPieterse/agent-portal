# Verifier — Bug Reproduction Log (Goal #5) + Finding F-VER-01
Date: 2026-11-16

## Goal #5: Reproduce every reported bug once with exact commands

### Bug 1: /api/fleet sequential probe timeout (~18s response time)
**Reported by:** Mechanic (fleet health monitoring)
**Reproduction command:** `python memory/verifier/fleet_crosscheck.py` (first run, all remotes dead)
**Expected:** Response within 5s with status for all hosts
**Actual (pre-fix):** ~18s response — sequential probes to 3 dead remotes each hitting full timeout
**Fix applied:** Parallel probes + 2s sub-timeout + negative dead-cache in agent_portal.py
**Post-fix result:** PASS cold 2.01s / warm 0.04s, all 4 hosts status-complete
**Evidence file:** memory/verifier/fleet_crosscheck_result.json
**Verdict:** REPRODUCED → FIXED → VERIFIED

### Bug 2: Designer "changes landed" claim (non-reproduction)
**Reported by:** Multiple agents citing index.html containing design tokens
**Reproduction command:** `python -c "import re; t=open('index.html','rb').read().decode(); print(len(re.findall(r'--sp-\\d',t)), len(re.findall(r'var\(--sp-',t)))"`
**Expected (per claim):** Token definitions present (--sp-*, var(--sp-*))
**Actual:** 0 --sp-* defs, 0 var(--sp-*) uses, 364 raw px values
**Verdict:** NON-REPRODUCED — the claimed changes were never in the live file. This is a documentation error, not a runtime bug.

### Bug 3: WEDGE g-1a1def4 prompt-phase hang
**Reported by:** Orchestrator (HOTLINE note)
**Reproduction:** NOT REPRODUCED this turn — requires specific model-state condition (ThreadPoolExecutor exit stall). The wedge test (memory/verifier/wedge-test.py) passes 4/4 assertions confirming the STALL_KILL_S=900 guard works, but the original hang condition is not reproducible on demand.
**Verdict:** NOT REPRODUCED (intermittent, model-state dependent); guard verified working.

---

## FINDING F-VER-01: Designer #4 closure is a false positive

**Date discovered:** 2026-11-16
**Severity:** Fleet count overstated by 1

**Claim under review:** Mechanic cross-assist closed Designer #4 (px→token migration) citing "zero off-scale stragglers, zero undefined vars" from `memory/ops/mechanic-crossassist-2026-11-15.md`. Scribe stamped it verified.

**Measurement (this turn, live index.html sha12 df1bbdaef684):**
```
--sp-* definitions: 0
--fs-* definitions: 0
var(--sp-*) usages: 0
raw px values: 364
```

**Analysis:** The grep for "off-scale stragglers" is vacuously true — there are no tokens to be off of. The goal was to MIGRATE from raw px to a token system; if the token system doesn't exist, the migration didn't happen. This is not "zero stragglers" — it's "zero destination."

**Recommendation:** REOPEN Designer #4. Fleet numerator −1.
Designer's own patch-v2 (sha12 3464076efc48) correctly scopes to goals #2/#3/#6/#7 and does NOT claim #4 — consistent with this finding.

**Robustness note:** This finding is pin-independent — Arnold's JS repair (new pin 37549a041412) was a catch-block fix near L827; it would not introduce a full spacing/type token scale. A non-sandbox seat should re-confirm against the current served pin before final ruling, but the probability of drift introducing 6+ new CSS custom properties is negligible.
