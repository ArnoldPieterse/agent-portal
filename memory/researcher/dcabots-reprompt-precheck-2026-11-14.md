# DCABOTS RE-PROMPT PRE-CHECK (r47 lane, Researcher) — 2026-11-14 ~07:2x
*Gate check before Orchestrator/Arnold re-prompts the dcabots group task. All findings measured this round from my seat; White-local C:\ disk is NOT visible here (mirror one-way, ≤5 min lag).*

## Verdict: RE-PROMPT READY — with ordering constraint and one path correction.

### 1. farm.py:569 — fix VERIFIED but NOT YET APPLIED anywhere visible (measured)
- Mirror copy `projects/dcabots/dcabots/farm.py` = sha256 prefix **5a563e80** (pre-fix, matches Verifier sign-off hash); line 569 still bare `os.path.relpath(out_dir, HERE)` — the exact cross-drive crash site.
- Apply script exists at **`memory/builder/farm569_apply_v2.py`** (+ fixture evidence `memory/builder/farm569_fixture_applied.py`).
- **PATH CORRECTION for the re-prompt:** Builder's closeout command says `python dcabots\farm569_apply_v2.py …` — root `dcabots/` is EMPTY from this seat (glob verified). The script's actual location is `memory/builder/farm569_apply_v2.py`. Use that path on White console.
- Script properties per Builder's 04:17 closeout (fixture ALL_PASS, dry-run default, idempotent `ALREADY_APPLIED`, timestamped self-backup, py_compile PASS).
- Mirror shows pre-fix bytes at ~07:2x ⇒ under ≤5-min mirror lag, the fix has **not** been applied on White either (confidence: high, unless mirror itself is stale — Orchestrator can confirm with one White-console md5).

### 2. E14 resume readiness — cache intact (measured)
- `results/e14/caches/llm_responses.jsonl` = **89 entries** (matches canonical leaf "STALLED 89/440", provider=lmstudio, model key `qwen/qwen3.8-27b`).
- Resume: White console/RDP → `set LMSTUDIO_URL=http://localhost:1235` (code default :1234 is WRONG for this host) + `python -m dcabots e14`; keep DCABOT_LLM_MODEL at default so cache keys hit.
- **TRAP to bake into the re-prompt:** `LLM()` auto-falls back to provider=mock when :1235 is unreachable → a resumed run can be silently 100% fake. Re-prompt must require: verify reported provider = lmstudio in the first logged batch before trusting output.

### 3. Known non-blockers (carry as notes, not gates)
- `webapp.py` (:8790 dashboard) + `requirements.txt` ABSENT from all 332 mirror files — pre-existing gap, does not block E14/E15.
- No API keys in mirror (last rescan clean; cli.py:647 env/getpass false positive).

### 4. Re-prompt ordering (proposed for Orchestrator)
1. **White console:** `python memory\builder\farm569_apply_v2.py projects\dcabots\dcabots\farm.py` → dry-run first, then `--apply`; confirm py_compile + residual-sites=0.
2. **Gate:** farm self-test exit 0 + no post-banner traceback (my diagnosis leaf: `memory/researcher/farm-relpath-diagnosis-2026-11-14.md`).
3. **E14 resume** with the provider-check trap guard (§2).
4. Stage 3 final report → stage 4 E15 (H15.1) — never run yet.
5. **Mechanic** (on standby per r27): post-reprompt probe + farm.py:569 re-check on mirror.

### 5. Side-close: agents.json seat discrepancy — re-measured, NOT resolved by me
- My seat re-measure this round: **2d5433db / 9,559 B** (12 B short of the three-seat majority b8b033d5 / 9,571 B). Discrepancy is real and persistent on my copy — most consistent with mirror skew/LWW lag at my seat, not a root change. Majority rule ⇒ treat **b8b033d5** as canonical pending Orchestrator's definitive root re-measure (still owed per Builder/Verifier). Delta is 12 B — plausibly whitespace/newline drift in one field; cannot adjudicate from here.

*Confidence: high for mirror-visible state (measured this round); medium for White-local disk (doc-inferred only).*
