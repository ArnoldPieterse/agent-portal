# OPS NOTE 2026-11-15 ~17:0x - Mechanic goal #3: reboot-recovery dry-run, remote legs

## Verdict: 2/3 PASS, 1 BLOCKED (firewall)

| Host | TCP :8888 | Studio API | Models loaded | Verdict |
|------|-----------|------------|---------------|---------|
| BLACK .99 | PASS (0.025s) | PASS (JWT login) | 5/7: Q4_K_S ctx65536, Q8_0 ctx32768, UD-Q4_K_S, builder-q8, verifier-q4 | **PASS** |
| PALE .39 | PASS (0.002s) | PASS (JWT login; Bearer key in pale_dl.py is STALE - 401) | 4/6: Q8_0 ctx32768, Q4_K_S ctx65536, archivist-q8, designer-q4 | **PASS** |
| RED .245 | FAIL (WinError 10013) | N/A | N/A | **BLOCKED** |

## RED block detail
- WinError 10013 ("access to a socket in a way forbidden by its access permissions") on ALL ports tested: 8888, 5985, 445, 3389.
- This is White's Windows Firewall blocking outbound TCP to Red specifically (Black/Pale reachable normally in same run).
- Not a host-down issue: the error is local (socket forbidden), not timeout or connection-refused.
- `ping` also fails with "Unable to contact IP driver" (ICMP outbound likely filtered globally).

## Fix needed (HUMAN GATE - requires admin on White)
```
netsh advfirewall firewall add rule name="LAN Red 245" dir=out action=allow remoteip=Red protocol=TCP
```
Or identify and remove the blocking rule:
```
netsh advfirewall firewall show rule name=all dir=out | findstr /i "245"
```
Then re-run: `python reboot_dryrun_remotes.py` from White.

## Broken-step fix (PALE)
- **What broke:** Bearer key `sk-lm-20522f7cdd1a46238d71e6b28e06761e` in `pale_dl.py` returns 401 "Invalid token payload" on /v1/models.
- **What fixed it:** JWT login (`POST /api/auth/login` with unsloth/[REDACTED-CREDENTIAL]) works identically to Black. The `fleet_reload.py` already uses this pattern for Pale (extracts key from pale_dl.py but the actual load calls use the JWT path). For probing, use JWT not Bearer.
- **Action:** Update `pale_dl.py` header comment or add a note that the Bearer key is stale; JWT is the working auth path.

## Runbook step mapping (per windows-runbook.md post-reboot verification order)
1. ~~nvidia-smi per-GPU VRAM~~ — not possible remotely without WinRM/RDP; covered by model-load evidence below
2. GET :8888/api/inference/status — BLACK PASS, PALE PASS, RED BLOCKED
3. Portal :8099 — N/A for remotes (no portal on Red/Pale/Black per host map)
4. Functional probe (models loaded) — BLACK 5 models, PALE 4 models = auto-start + fleet_reload working

## Evidence files
- `reboot_dryrun_remotes.py` — round 1 script (all 3 hosts, Bearer auth)
- `reboot_dryrun_r2.py` — round 2 fix (Pale JWT + Red WinRM attempt)
- Timestamp: 2026-11-15 17:05:28 (round 1), 17:05:58 (round 2)

---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
