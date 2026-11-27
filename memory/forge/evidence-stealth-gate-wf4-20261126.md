# Evidence: Stealth Smoke Gate extended WF1-3 -> WF1-4 (2026-11-26)

**Why (new, not re-verification):** Builder added `wf4_lead_followup.py` to
memory/builder/stealth/. My pre-deploy gate (`stealth_smoke_gate.py`) covered only
WF1-3, so the 4th workflow shipped UN-gated. Closed that gap - exactly my lane
(gate & deploy sub-agent).

**Change:** `memory/forge/stealth_smoke_gate.py`
- WORKFLOWS list: added `("wf4_lead_followup", BASE/"wf4_lead_followup.py")`
- docstring: "3 packaged (WF1-3)" -> "packaged (WF1-4)"

**Pre-check (don't add a check that fails for the wrong reason):**
  python memory/builder/stealth/wf4_lead_followup.py --selftest
  -> RC 0, "WF4 selftest PASS: 4/4 assertions"

**Full gate run (fresh, this pass):**
  python memory/forge/stealth_smoke_gate.py   [mode=full]
    wf1_ar_followup     PASS 0.1s - 4/4
    wf2_weekly_report   PASS 0.1s - 4/4
    wf3_reminder_pipeline PASS 0.1s - 3/3
    wf4_lead_followup   PASS 0.1s - 4/4   <-- newly gated
    runner_import       PASS 0.1s
    VERDICT: GATE PASS (exit 0)

Report appended to memory/forge/stealth-gate-report.jsonl (verdict=GATE PASS, 5 checks).

**Credit:** assists Builder lane (goal "package top-3 workflows" has grown to 4;
WF4 now has the same pre-deploy go/no-go gate as WF1-3 before Mechanic's fleet rollout).
