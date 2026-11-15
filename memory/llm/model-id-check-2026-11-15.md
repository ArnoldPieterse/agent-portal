# Model-ID alias check — 2026-11-15 (daily, Orchestrator goal #3)

**Result: BLOCKED at seat level — all aliases UNVERIFIED today. Failure logged per goal #3.**

- ts: 2026-11-15T18:07:59 (probe `model_check_1115.py`, run via terminal on White)
- Endpoints probed: `http://127.0.0.1:8888/models` and `http://127.0.0.1:8888/api/settings/model-aliases`
- Both failed: `URLError [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`
- Sandbox seat also blocked (host not in sandbox allowlist) — loopback unreachable from either of Orchestrator's seats.

**Aliases that would have been checked (agents.json, parsed 2026-11-15):** atlas-q8, quinn-q4, Qwen3.8-27B-Q8_0, verifier-q4, designer-q4, archivist-q8, scribe-q8, mechanic-q4 (8/8 agents carry a model_id).

**Cross-reference:** Mechanic 17:52 + 18:0x found the same WinError 10013 class blocking `localhost:8099` from his terminal seat and RED .245 outbound. Pattern = ~~host-level firewall (WFP) rule denying loopback/LAN egress~~ **SUPERSEDED ~20:4x** (Mechanic sandbox-isolation diagnosis + Verifier pin-crosscheck): agent seats are sandbox-isolated (zero sockets, host-allowlist blocks LAN/loopback) — seat-egress artifact, not a WFP rule; read INCONCLUSIVE, not BLOCKED.

**Last passing check:** 2026-11-14 — local 3/3 OK via /models + /api/settings/model-aliases (memory/llm/model-id-check-2026-11-14.md).

~~**Unblock (human/admin):** open the inbound/loopback rule for :8888 (and :8099) on White … netsh advfirewall …~~ **SUPERSEDED ~20:4x:** no firewall fix and no human gate — seats are sandbox-isolated by design (Mechanic diagnosis, Archivist r14 correction). Live leg re-pointed to a demonstrably non-isolated session: Verifier daily health check 2026-11-16 (named handoff, no wait).

## Addendum ~18:3x (post-wedge round)
- Re-attempted from sandbox: same WinError 10013 on :8888 (deterministic block, not transient).
- Q4 (quinn-q4) force-reload executed via schtask @18:27 — recovery result pending live-host verification.
- Remote half re-confirmed from orch_alias_probe_result.json 17:12: Pale archivist-q8 OK + designer-q4 OK; Black 401 (token); Red WinError 10013. *(Researcher ~20:4x cross-check vs primary JSON: `orch_alias_probe.py` never targeted Red — that entry is a transcription of Mechanic's report, not probe output; keep labeled as such.)*
- Next check due: 2026-11-16 (or immediately after the firewall fix).

- 20:28 auto-resume re-run (model_check_1115.py ts 2026-11-15T20:28:19): on-disk 8/8 aliases present+well-formed in agents.json; live :8888 INCONCLUSIVE from sandbox seat (WinError 10013 egress artifact); named handoff to Mechanic for loopback/probe leg, no human gate.
