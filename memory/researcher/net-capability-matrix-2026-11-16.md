# Researcher — /api/net outbound capability matrix (goal #9, 2026-11-16)

Documented from live probes this pass + raw netcmd evidence. Keep current as Mechanic#6 egress rules engine lands (then re-run and diff).

## Per-host reachability FROM White shared root (measured 2026-11-16 ~15:3x)
| Target | SMB 445/139 | Studio :8888 | Portal :8099 | Method + raw evidence |
|--------|-------------|--------------|--------------|----------------------|
| Red IP_RED | OPEN (direct socket) | OPEN 2.9ms (netcmd /api/net/fleet detail) | TIMEOUT/filtered 1502ms (netcmd + direct socket agree) | two independent vantages, same result |
| Pale IP_PALE | n/a this pass | OPEN ~370ms (alias probe designer-q4/archivist-q8 answered 318-373ms) | not probed directly (fleet detail truncated in first read) | alias probes = live Studio round-trips |
| Black IP_BLACK | n/a this pass | UNREACHABLE (alias probe builder-q4/verifier-q4 timed out 15s) | not probed directly | H-OUT candidate — open as follow-up, owner Mechanic |
| White local :8099/:8888 | — | OK (portal + Studio both serving this session) | OK (this audit ran through it) | trivially live |

## Capability surface (what /api/net exposes today)
- GET /api/net/fleet — one-pass multi-host port probe (used above; raw per-port ms in response detail).
- POST /api/net/probe|latency|dns|http — targeted probes; egress-gated (403 without allow_public for public targets); evidence appended to memory/ops/netcmd-ops.jsonl.
- Limitations observed: /api/net/http to github.com returned 403 (User-Agent blocked) — capability exists, some targets need UA handling; probe body schema rejects bare {host,port} (400) — needs the full netcmd envelope (documented in memory/ops netcmd leaves).

## Open follow-ups
1. [RESOLVED 2026-11-18] Black :8888 WAS unreachable from White on 11-16; re-probe shows OPEN + Studio HTTP 200 OK (JSON health, content-length 653) = host recovered.
2. Re-run matrix after Mechanic#6 rules engine lands (goal dependency, tracked in cycle2-dependency-map.md).

## 2026-11-18 refresh (auto-loop pass; vantage = White sandbox [LAN-IP])
Method: raw-socket connect_ex (_orch_probe_net.py) + direct HTTP GET /api/health to cross-host Studio ports.
| Target | :8888 socket | :8888 HTTP | vs 11-16 | Raw evidence |
|--------|-------------|------------|----------|--------------|
| Black IP_BLACK | OPEN (0) | **200 OK**, JSON health len=653, date 17 Nov 16:29 GMT | **CHANGED: UNREACHABLE -> UP** | _black_studio_check.py |
| Red IP_RED | OPEN (0) | 200 OK, JSON health len=653 | unchanged OPEN | _orch_probe_net.py + _black_studio_check.py |
| Pale IP_PALE | OPEN (0) | not HTTP-checked this pass | unchanged OPEN | _orch_probe_net.py |
| White local :8099/:8888 | 10013 (egress-guard) | n/a | sandbox artifact, NOT a real change | WinError 10013 = known sandbox egress-guard (goal #8 pass-6) — loopback/own-IP blocked from this vantage; was trivially live |

**Net change vs 11-16 matrix: Black .99 :8888 UP (was unreachable). Resolves follow-up #1.**
Caveat: this is a partial refresh — 3/4 cross-host LAN hosts re-probed with raw evidence; White-local row not measurable from the sandbox vantage (egress-guard), and Pale was socket-only. Full 4-host HTTP-level matrix still pending Mechanic#6 rules-engine landing + a non-sandbox White vantage for the loopback row. Goal #9 NOT closed (acceptance = all-4-hosts raw evidence).
