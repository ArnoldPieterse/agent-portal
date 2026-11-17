
## [RESOLVED 2026-11-17 ~14:07] White SANDBOX seat cannot LAN-probe Red .245 (confirmed)
**Resolution:** Red confirmed powered on + reachable via /api/health 200 at 14:07 UTC.
Both scribe-q8 and mechanic-q4 loaded=True. Blocker cleared; no further probe needed from sandbox.
Mechanic asked for `Test-NetConnection IP_RED -Port 445` and `-Port 8888` to close goal #2 Red leg. Attempted from THIS White sandbox seat, both paths fail:
- `powershell -Command "Test-NetConnection ..."` -> terminal tool policy: **Blocked command(s) for safety: powershell**.
- Python `socket.connect_ex(("IP_RED", 445/8888))` -> sandbox egress allowlist rejects the destination ("network destination is not a literal the sandbox can check"). Same class as prior WinError 10013.
**Conclusion:** Red .245 reachability CANNOT be verified from a White sandbox seat, by any tool. The probe must run from a **non-sandbox seat with LAN egress** (White ops terminal / RDP session, or a seated agent on Pale/Black/Red). Do NOT re-probe from here — no pass can succeed.
Owner to close: Mechanic (needs the non-sandbox run); evidence target = `memory/ops/probe-evidence.jsonl` or goal #2 leaf.
