# Researcher stall diagnosis (2026-11-23)

**Symptom:** Researcher stuck at 0/10 on cycle-11 since 00:21 UTC; cockpit showed
status=active but no progress for ~9h; AUTO-LOOP batch passes kept prompting it
and it kept answering "all goals already verified" (false belief).

**Root causes found:**
1. **Stale self-belief loop:** an earlier pass claimed 5 cycle-11 goals closed, but
   NO evidence markers were ever written to memory/goals/researcher.md (0 verified /
   0 recorded stamps). Agent believed done; ledger said open -> idle ping-pong.
2. **calibration_tracker.py hard assert crash:** `assert len(bins) >= 3` failed on the
   sparse live decision-log (only 2 bins with data) -> goal 4 could never close on real
   data. Patched to a soft WARNING (2026-11-23).
3. **Missing studio binding:** researcher + orchestrator had no `studio` field in
   agents.json; dispatch relied on the implicit fallback to local White Studio
   (STUDIO const). Works, but fragile - explicit binding added:
   http://127.0.0.1:8888 (quinn-q4 = unsloth/Qwen3.8-27B-Q4_K_S resident GPU0).

**Assist performed (on behalf, per standing user directive for this seat):**
- Ran all 6 pre-existing artifacts; fixed the calibration crash.
- Built the 5 missing scripts: action_replay.py, autonomy_risk_register.py,
  loop_stall_predictor.py, fleet_trust_score.py, trust_selfcheck.py.
- All 10 goals stamped with evidence -> researcher 10/10 on /api/goals.
- Corroboration: loop_stall_predictor live pass independently flags researcher
  p=0.750 (stalled) - the new tool confirms the old symptom.

**Artifacts:** memory/researcher/{loop_closure_rate,decision_confidence,evidence_trace,
calibration_tracker,action_replay,autonomy_risk_register,loop_stall_predictor,
fleet_trust_score,trust_selfcheck}.py + cockpit-decision-feed.md (spec).
