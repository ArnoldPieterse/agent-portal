# Researcher — /api/net outbound capability matrix (goal #9, 2026-11-16)

Documented from live probes this pass + raw netcmd evidence. Keep current as Mechanic#6 egress rules engine lands (then re-run and diff).

## Per-host reachability FROM White shared root (measured 2026-11-16 ~15:3x)
| Target | SMB 445/139 | Studio :8888 | Portal :8099 | Method + raw evidence |
|--------|-------------|--------------|--------------|----------------------|
| Red 192.168.1.245 | OPEN (direct socket) | OPEN 2.9ms (netcmd /api/net/fleet detail) | TIMEOUT/filtered 1502ms (netcmd + direct socket agree) | two independent vantages, same result |
| Pale 192.168.1.39 | n/a this pass | OPEN ~370ms (alias probe designer-q4/archivist-q8 answered 318-373ms) | not probed directly (fleet detail truncated in first read) | alias probes = live Studio round-trips |
| Black 192.168.1.99 | n/a this pass | UNREACHABLE (alias probe builder-q4/verifier-q4 timed out 15s) | not probed directly | H-OUT candidate — open as follow-up, owner Mechanic |
| White local :8099/:8888 | — | OK (portal + Studio both serving this session) | OK (this audit ran through it) | trivially live |

## Capability surface (what /api/net exposes today)
- GET /api/net/fleet — one-pass multi-host port probe (used above; raw per-port ms in response detail).
- POST /api/net/probe|latency|dns|http — targeted probes; egress-gated (403 without allow_public for public targets); evidence appended to memory/ops/netcmd-ops.jsonl.
- Limitations observed: /api/net/http to github.com returned 403 (User-Agent blocked) — capability exists, some targets need UA handling; probe body schema rejects bare {host,port} (400) — needs the full netcmd envelope (documented in memory/ops netcmd leaves).

## Open follow-ups
1. Black :8888 unreachable from White today (new since 11-15 "3/3 up") — Mechanic to check Black Studio process; H-OUT line if confirmed down.
2. Re-run matrix after Mechanic#6 rules engine lands (goal dependency, tracked in cycle2-dependency-map.md).
