# Red: powered-on but LAN-unreachable (2026-11-25)

Human: "red is powered on." Probe from White sandbox seat (TCP, ICMP blocked here - IP driver failure).

## Evidence
| target | port | result |
|---|---|---|
| Red IP_RED | 3389/445/5985/8888 | all CLOSED/DROP |
| Pale IP_PALE (control) | 445 | OPEN 27ms |
| Black IP_BLACK (control) | 445 | OPEN 16ms |

## Verdict
Egress is FINE (controls answer ~20ms). Red-specific: every TCP port drops incl :445 SMB.
"Powered on" (power/BIOS) != "on the network." Same cold-host-despite-power signature as prior notes.
Likely: NIC not up / still booting / IP changed / switch-port down.

## Action taken
Stayed on White/Pale/Black seats for any home-model work. No lane blocked - Red seats (Scribe, Mechanic) already relocated per run start.
Unblock if Red is needed: confirm NIC+IP from a physical/RDP seat; then re-probe :445 then :8888.
