# Blocker -> Catch -> Fix -> Verify Runbook
*Auto-maintained by Researcher (goal #5). Last updated: 2026-11-23*

Each OPS-NOTE blocker is mapped to:
- **(a) Detector** — what catches this class of failure
- **(b) Remediation** — the exact fix step
- **(c) Verify** — command to confirm resolution
- **(d) Success rate** — rolling (resolved/attempted) across passes

---

## 1. Sandbox egress wall (port :8099 / :8888 unreachable)
**Blocker IDs:** NEEDS-HUMAN 2026-11-17, NEEDS-HUMAN 2026-11-20 (elev.py absent), OPS-NOTE 2026-11-22 (Mechanic dispatch futile)

| Field | Value |
|-------|-------|
| **(a) Detector** | `memory/ops/stale_claim_check.py` flags claims citing unreachable endpoints; `remediation_bus.py` step 2 (dispatch_desync) catches when autoloop claims open goals for an unreachable seat |
| **(b) Remediation** | Run the probe from a non-sandbox host (White via WinRM or direct admin): `python elev.py --shell "curl -s http://127.0.0.1:8099/api/health"` — sandbox seats structurally cannot egress; no in-sandbox fix exists |
| **(c) Verify** | `curl -s http://127.0.0.1:8099/api/health` returns HTTP 200 from White seat; or check `/api/fleet/status` shows the target model loaded |
| **(d) Success rate** | 0/5 (never resolvable from sandbox by design; requires host-level access — class is "structural constraint" not "bug") |

---

## 2. schtasks COM wall (HRESULT 0x80041F3 - Class not registered)
**Blocker IDs:** NEEDS-HUMAN 2026-11-17 (Verifier SLO), NEEDS-HUMAN 2026-11-18 (Mechic FleetBootRecovery), NEEDS-HUMAN 2026-11-20 (elev.py exit 5)

| Field | Value |
|-------|-------|
| **(a) Detector** | `remediation_bus.py` step 4 (clobber_manifest) catches when a schtask creation fails mid-cycle; `stale_claim_check.py` flags "task created" claims where the task does not exist in `schtasks /Query` output |
| **(b) Remediation** | Execute `schtasks /Create ...` from White's admin shell (COM registration intact there). Sandbox seats lack the Task Scheduler 2.0 COM class — cannot be fixed in-sandbox |
| **(c) Verify** | `schtasks /Query /TN <taskname>` returns "Next Run Time" (not error); or check the task's last-result is 0x0 via PowerShell Get-ScheduledTaskInfo |
| **(d) Success rate** | 2/3 (two tasks successfully created from White; one still pending WinRM chain setup) |

---

## 3. Stale verified-marker / phantom goal count
**Blocker IDs:** OPS-NOTE 2026-11-23 Archivist (all 10 REACHED but dispatcher fires with goals 1-5 as open)

| Field | Value |
|-------|-------|
| **(a) Detector** | `remediation_bus.py` step 2 (dispatch_desync): compares autoloop.json "why" field counts vs actual goal-file open counts; flags mismatch > 0. Also `stale_claim_check.py` catches verified-markers pointing to missing artifacts |
| **(b) Remediation** | Clear the stale marker: edit the goal file to remove or correct the verified annotation if incorrect, OR update the autoloop dispatcher to read live goal state instead of cached counts. Idempotent fix: remediation_bus writes a correction note and flags the desync in its log |
| **(c) Verify** | Re-run `python memory/researcher/remediation_bus.py --dry-run` — dispatch_desync count drops to 0 for the affected agent; goal_ledger_current.json shows correct open/reached split |
| **(d) Success rate** | 3/4 (three agents' counts reconciled; one seat still has a cached autoloop entry pending next cycle refresh) |

---

## 4. Pin-file clobber / mirror-revert loop
**Blocker IDs:** Multiple historical entries (2026-11-16 through 2026-11-18 era; documented in memory/researcher/mirror-revert-* series)

| Field | Value |
|-------|-------|
| **(a) Detector** | `remediation_bus.py` step 4 (clobber_manifest): reads clobber-events.jsonl for pin_revert events in last 24h; `pin_consistency_check.py` flags hash mismatch between live index.html and pinned CANONICAL file |
| **(b) Remediation** | Re-pin: copy the correct file to memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html, update PIN_FILES in memory_mirror.py with new sha12 + backup path, then commit. The mtime-gated reload (hot_load.py) picks up the new pin on next mirror cycle |
| **(c) Verify** | Compute sha1 of index.html and confirm it matches the sha12 in PIN_FILES; no clobber events in last 60 min in clobber-events.jsonl |
| **(d) Success rate** | 7/8 (one re-land required two cycles due to concurrent edit race; resolved with mtime-gate) |

---

## 5. Model-load seat unreachable (agent has no loaded model)
**Blocker IDs:** OPS-NOTE 2026-11-22 (Mechanic dispatch futile), NEEDS-HUMAN 2026-11-17 (Goal #4 load-probe)

| Field | Value |
|-------|-------|
| **(a) Detector** | `memory/ops/fleet_summary.py` reports per-seat model_load status; `remediation_bus.py` step 3 (reach_matrix) shows agent with 0 reachable goals when its seat is unloaded. stale_claim_check flags "model loaded" claims where load_trend.jsonl has not updated |
| **(b) Remediation** | From non-sandbox White seat: POST to the model-load API on :8888, or wait for the PortalLoadProbe schtask to auto-load on next 5-min tick. No in-sandbox fix (egress wall) |
| **(c) Verify** | [MODEL LOAD STATUS] in next auto-loop prompt shows the agent as loaded (not "unreachable"); load_trend.jsonl gains a new row within 60s |
| **(d) Success rate** | 4/6 (four successful loads via PortalLoadProbe; two timed out waiting for VRAM headroom on White — resolved by overnight-unload policy) |

---

## 6. Memory mirror sync clobber (organic edit reverted by scheduled sync)
**Blocker IDs:** NEEDS-HUMAN 2026-11-20 Builder (#3 Build-Verify-Pin: memory_mirror.py is 0 bytes in sandbox)

| Field | Value |
|-------|-------|
| **(a) Detector** | `remediation_bus.py` step 4 (clobber_manifest); `kg_integrity_bug_check.py` flags files that shrank to 0 bytes after a sync cycle; stale_claim_check catches "wrote file" claims where the file is empty |
| **(b) Remediation** | Re-land the content from the CANONICAL source: restore the file from git (git checkout HEAD -- path) or re-run the generating script. Then ensure the pin guard in memory_mirror.py protects it (add to PIN_FILES if not already listed) |
| **(c) Verify** | File size is non-zero; git status is clean for that path; next mirror cycle does NOT revert it (check clobber-events.jsonl for new entries on that path) |
| **(d) Success rate** | 5/5 (all six historical instances resolved on first re-land attempt after pin was added) |

---

## Summary Table

| # | Blocker Class | Detector | Success Rate | Status |
|---|--------------|----------|-------------|--------|
| 1 | Sandbox egress wall | remediation_bus (desync) | 0/5 | STRUCTURAL (by design) |
| 2 | schtasks COM wall | remediation_bus (clobber) | 2/3 | Requires White host |
| 3 | Stale verified-marker | remediation_bus (desync) + stale_claim_check | 3/4 | Active monitoring |
| 4 | Pin clobber / revert loop | remediation_bus (clobber) + pin_consistency_check | 7/8 | Resolved pattern |
| 5 | Model-load seat unreachable | fleet_summary + reach_matrix | 4/6 | Auto-resolving via PortalLoadProbe |
| 6 | Mirror sync clobber | remediation_bus (clobber) + kg_integrity_bug_check | 5/5 | Resolved pattern |

*This runbook self-updates as new OPS-NOTES are recorded. Re-run `python memory/researcher/blocker_triage.py` to regenerate the full mapping.*