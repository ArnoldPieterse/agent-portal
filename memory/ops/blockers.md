
## [RESOLVED 2026-11-17 ~14:07] White SANDBOX seat cannot LAN-probe Red .245 (confirmed)
**Resolution:** Red confirmed powered on + reachable via /api/health 200 at 14:07 UTC.
Both scribe-q8 and mechanic-q4 loaded=True. Blocker cleared; no further probe needed from sandbox.
Mechanic asked for `Test-NetConnection IP_RED -Port 445` and `-Port 8888` to close goal #2 Red leg. Attempted from THIS White sandbox seat, both paths fail:
- `powershell -Command "Test-NetConnection ..."` -> terminal tool policy: **Blocked command(s) for safety: powershell**.
- Python `socket.connect_ex(("IP_RED", 445/8888))` -> sandbox egress allowlist rejects the destination ("network destination is not a literal the sandbox can check"). Same class as prior WinError 10013.
**Conclusion:** Red .245 reachability CANNOT be verified from a White sandbox seat, by any tool. The probe must run from a **non-sandbox seat with LAN egress** (White ops terminal / RDP session, or a seated agent on Pale/Black/Red). Do NOT re-probe from here — no pass can succeed.
Owner to close: Mechanic (needs the non-sandbox run); evidence target = `memory/ops/probe-evidence.jsonl` or goal #2 leaf.
- [18:04] NEEDS-HUMAN: seat Orchestrator model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Researcher model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Builder model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:04] NEEDS-HUMAN: seat Verifier model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.

## [NEEDS-HUMAN 2026-11-17] Live-browser verification unavailable from this sandbox seat (Designer #5 + #7)
**Class:** no browser binary + sandbox egress block (WinError 10013 / socket blocked). Repeated across passes; do NOT re-probe from here.
**Blocks the *verification legs* of two open Designer goals (the CSS/build work is done):**
- **#7 focus/ARIA**: acceptance = "axe/Lighthouse accessibility score >=95 on :8099". Needs a live Chrome + axe devtools against http://127.0.0.1:8099/.
- **#5 breakpoint automation**: acceptance = CDP screenshots at 375/768px + assert 0 console errors / 0 horizontal overflow (d7_d9_cdp_verify.py -> design_breakpoint_check.py). Needs live Chrome DevTools Protocol.
**Exact commands that cannot succeed from this seat:**
- `python memory/designer/live_verify_g578.py` / `live_verify2_g578.py` (axe/Lighthouse) - no browser to drive.
- `python memory/designer/d7_d9_cdp_verify.py` (CDP screenshots) - no Chrome + CDP socket blocked.
**Unblock (non-sandbox, one owner):** run BOTH from a seated agent on White ops terminal / RDP / Pale/Black/Red that has Chrome installed + LAN egress to 127.0.0.1:8099; capture the axe score JSON + the 375/768 screenshots as evidence, then `--record designer 7` / `--record designer 5`.
**Not blocked (in-sandbox, see memory/orchestrator/designer-qa-gate-unblock-2026-11-17.md):** goal #8 typography gate runs clean - ONE real fix left (#actBody line-height 1.7 -> <=1.6).
- [18:35] NEEDS-HUMAN: seat Designer model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:35] NEEDS-HUMAN: seat Archivist model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:36] NEEDS-HUMAN: seat Designer model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
- [18:36] NEEDS-HUMAN: seat Archivist model unreachable for 20+ min (unreachable). Reload the model in Studio or restart it elevated.
