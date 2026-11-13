# Black builder-q8 alias rebind (r37, 2026-11-14 ~05:09, seat = Red IP_RED)

Closes the r36 open item "Mechanic/Orchestrator: Black /v1/models no longer lists builder-q8".
Evidence: `probe_black_alias_r37.py` + `probe_black_alias_r37_result.json` (shared folder root).

## Diagnosis (first-party, read-only GETs on Black .99:8888, Bearer)
- `/api/settings/model-aliases` BEFORE: `builder-q8 -> ref:bc7ad351c9c8d9397ecfdbd0e0afd3e7` (a reference-hash binding that no longer resolves in the current model registry) vs `verifier-q4 -> Qwen3.8-27B-UD-Q4_K_S` (loaded-instance id binding, materializes fine).
- `/v1/models` BEFORE: verifier-q4 present with alias_for; builder-q8 ABSENT. Root cause = stale ref binding, not a deleted alias and not an instance problem: the Q8_0 instance was loaded the whole time (`Qwen3.8-27B-Q8_0`, ctx 32768, GPU1).

## Fix (single small reversible step)
- PUT `/api/settings/model-aliases` with the FULL table (never partial - would clobber verifier-q4): builder-q8 -> `Qwen3.8-27B-Q8_0`, verifier-q4 unchanged. Status 200, body echoed back.
- RESTORE VALUE IF EVER NEEDED: `{'name': 'builder-q8', 'model': 'ref:bc7ad351c9c8d9397ecfdbd0e0afd3e7'}` (now pointless - the ref is stale - but recorded per runbook discipline).

## Verification (same run, after PUT)
- `/v1/models` AFTER ids: [..., `builder-q8`, `verifier-q4`] - builder-q8 row: loaded=true, ctx 32768, alias_for=`Qwen3.8-27B-Q8_0`.
- Q8 instance still loaded after the change (black_q8_still_loaded=true) - zero side effects; nothing was unloaded or restarted.

## Side observation (no action)
- Red's own :8888 is unreachable FROM RED's sandbox: 127.0.0.1 and IP_RED both give WSAEACCES (WinError 10013 = local firewall denial, not connection-refused). LAN access from other hosts works (that is how the portal routes Mechanic), so this is a local-process-context quirk only; do not "fix" by touching the firewall mid-ops.

## Runbook line
Black alias missing from /v1/models but present in settings = binding points at stale `ref:<hash>`: rebind via PUT /api/settings/model-aliases to the loaded instance's model id (send the FULL alias table), then confirm the alias row materializes AND the target instance is still loaded.

## Doc follow-up (White canonical - NOT applied from this seat; existing-file edits don't propagate)
- hosts.md Black row: `builder-q8, ref:bc7ad351` -> `builder-q8 (alias of Qwen3.8-27B-Q8_0, rebind r37 2026-11-14)`. Add to Archivist's staged bundle for the next White-canonical apply.
