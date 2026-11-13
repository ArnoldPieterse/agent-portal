# Verifier r28 — AC-A2-2 LIVE check[1] expectation ratification (2026-11-14 ~05:5x)

## First-party verification (this seat, canonical source)
- `agent_portal.py` L1371–1386 (`/api/uploads`): `os.walk(UPLOAD_DIR)` **recursive**, adds **files only** (dirs excluded), row = `{path, size, mtime}`, response capped at **2000 rows**. Confirms Researcher r27's semantics claim from source; their file-count of 5,379 under White uploads/ stands as first-party (White disk unreachable from agent seats — egress re-proven).
- Consequence: strict `len(rows) == 1` is unmeetable while White's local (per-seat, un-mirrored) uploads/ holds pre-existing files. N=1 was a clean-room convenience assumption, NOT part of AC-A2 acceptance semantics.

## Ruling
- **RATIFIED — amended check[1]**: PASS = `status==200 AND ('uploads/_canary_remote.txt', 212) in rows` (N≥1). Property under test = canary visibility + identity through the portal API. Check[2] tightened to full pin: 200 + exactly 212 B + md5 `512d0dc8e96773b7db5574da4f0ae9f3`. Leg 3 (console-clean, devtools) unchanged.
- **REJECTED — option (b)** (destructive-clean of White uploads/, ~5,379 files incl. un-mirrored git bundle): data-loss risk on non-mirrored artifacts for zero test-value gain.

## Applied (this seat)
- `memory/mechanic/ac_a2_live_leg_r20.py` edited in place: check[1] amended, check[2] md5-tightened, docstring updated. py_compile OK; simulated payload (n=22 incl. canary) → pass=True.
- New pin: **2,822 B / md5 `803c6473f3262b02499c1abdd6dee705`** (was 2,341 B / `46f529dde45b21276be49a6ce1bd8e15`).
- **Propagation caveat**: if the mirror does not carry this edit to White (r25 rollback precedent), hand-apply on White before Arnold runs: replace the `uploads_list` pass line with `"pass": st == 200 and canary in rows` where `canary = ("uploads/_canary_remote.txt", 212)` is defined above it, and add `and hashlib.md5(body).hexdigest() == "512d0dc8e96773b7db5574da4f0ae9f3"` to the `raw_fetch` pass line. Verify md5 803c6473… on White first.

## Flags (evidence, for Orchestrator/Scribe/Researcher)
- Researcher's claimed leaf `memory/researcher/r27-probe-n-semantics-2026-11-14.md` is **ABSENT on my seat** (no r27 file in memory/researcher/; newest = ac-a2-r26-convergence-check + hosts-ctx-correction). Findings stand in-chat and are now independently re-verified from source by me.
- Scribe's round record also did not land (no scribe leaf newer than 11-13 files on my seat) after their truncated turn.

## Lane state
- AC-A2-1 / 2-static / 3 / 4: CLOSED per r19+r26. AC-A2-2 LIVE: sole owner = Arnold's three White-console legs (canary placement w/ sole-entry note now moot for N semantics — canary just needs to EXIST in uploads/, any subpath depth irrelevant since walk is recursive; run amended probe; devtools console-clean). When `ac_a2_live_leg_r20_result.json` lands with all checks pass + console-clean evidence, I accept in one step and the gate closes.
