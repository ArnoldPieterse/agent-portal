# Host Documentation Consistency Report
Generated: 2026-11-16T05:13:17.303783+00:00
Files scanned: 486
Total claims: 3076

## Summary by Host
| Host | Claims |
|------|--------|
| Red | 657 |
| Pale | 373 |
| Black | 527 |
| White | 1519 |

## Summary by Type
| Type | Count | Verification Method |
|------|-------|-------------------|
| file_path | 1252 | SMB path existence check |
| reference | 1213 | Manual review |
| port | 315 | TCP connect probe |
| endpoint | 189 | HTTP GET via fleet API |
| status | 107 | Fleet status endpoint |

## Verification Plan
- [ ] Run `--verify` when portal :8099 is reachable
- [ ] TCP probes for port claims (Mechanic fleet probe covers this)
- [ ] SMB path checks via Mechanic mirror spot-check
- [ ] Manual review pass for 'reference' type claims

## Priority Claims (verify first)

| ID | Host | Type | Claim | Verify |
|----|------|------|-------|--------|
| HC-0007 | White | endpoint | - [ ] 9. Post-consolidation prune dry-check: confirm the goal-collection section... | `GET http://white:8099api/todo/prune` |
| HC-0019 | White | port | - **White** = primary host; runs agent_portal.py (:8099), all shared files live ... | `TCP connect white:8099` |
| HC-0028 | Black | port | 3. Designer's r72 correction leaf cites "Fact (Verifier, serving seat): root the... | `TCP connect black:01` |
| HC-0029 | White | port | 3. Designer's r72 correction leaf cites "Fact (Verifier, serving seat): root the... | `TCP connect white:01` |
| HC-0063 | Pale | port | - Current `agent_portal.py` on Pale seat: first-1600-chars md5 = **ae20e867**fb5... | `TCP connect pale:37` |
| HC-0066 | White | port | - If mirror mtimes are preserved from source, the file's last edit (~13:37) pred... | `TCP connect white:37` |
| HC-0067 | Pale | port | - Record discrepancy (2026-11-13, Archivist): the L27 baseline 2ba0b031… does no... | `TCP connect pale:37` |
| HC-0068 | Black | port | - Record discrepancy (2026-11-13, Archivist): the L27 baseline 2ba0b031… does no... | `TCP connect black:37` |
| HC-0069 | White | port | - Record discrepancy (2026-11-13, Archivist): the L27 baseline 2ba0b031… does no... | `TCP connect white:37` |
| HC-0159 | Pale | port | State (superseded): 2026-11-13 (auto-continue r42, prompt x3 same round) - fresh... | `TCP connect pale:8888` |
| HC-0160 | White | port | State (superseded): 2026-11-13 (auto-continue r42, prompt x3 same round) - fresh... | `TCP connect white:8888` |
| HC-0161 | Pale | port | State (superseded): 2026-11-13 (auto-continue r41) - fresh sweep from Pale: NO N... | `TCP connect pale:8888` |
| HC-0162 | White | port | State (superseded): 2026-11-13 (auto-continue r41) - fresh sweep from Pale: NO N... | `TCP connect white:8888` |
| HC-0164 | Pale | endpoint | State (superseded): 2026-11-13 (auto-continue r39, portal-update planning meetin... | `GET http://pale:8099api/fleet` |
| HC-0165 | White | endpoint | State (superseded): 2026-11-13 (auto-continue r39, portal-update planning meetin... | `GET http://white:8099api/fleet` |
| HC-0196 | White | port | - Portal DOWN (:8099 closed) — human: schtasks /run /tn PortalRun on White.... | `TCP connect white:8099` |
| HC-0213 | Red | endpoint | - [ ] RED :8888 NOT LISTENING on LAN (r15 16:15:46 + Mechanic re-probe 16:59 - s... | `GET http://red:8099api/settings/lan-access/start` |
| HC-0221 | Red | port | `OPEN: Red :8888 web not bound (r15) — Arnold RDP fix; P0/P1 apply + UI port rem... | `TCP connect red:8888` |
| HC-0222 | White | port | `OPEN: Red :8888 web not bound (r15) — Arnold RDP fix; P0/P1 apply + UI port rem... | `TCP connect white:8888` |
| HC-0241 | Pale | port | - [x] 2026-11-13 r42 (auto-continue, prompt x3 same round): fresh sweep from Pal... | `TCP connect pale:8888` |