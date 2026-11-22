# Mechanic Goal 6 — Egress Guard Rules Engine
Date: 2026-11-16 ~21:14
Status: **IMPLEMENTED + test matrix PASS**

## What was built
`egress_guard.py` (root) + `egress-rules.json` (auto-generated defaults):
- Per-host allowlist: 4 fleet IPs + loopback, each with explicit allowed_ports
- Per-domain allowlist: github.com, api.openai.com, huggingface.co on :443
- Default policy: deny (fail-closed)
- Every check() call logs to `memory/ops/egress-audit.jsonl` with verdict + one-line reason

## Test matrix result (10 cases)
| # | target | port | verdict | correct |
|---|--------|------|---------|----------|
| 1 | Black | 8888 | ALLOW | ✓ |
| 2 | Black | 445 | ALLOW | ✓ |
| 3 | Black | 22 | DENY | ✓ |
| 4 | 127.0.0.1 | 8099 | ALLOW | ✓ |
| 5 | 127.0.0.1 | 8080 | DENY | ✓ |
| 6 | github.com | 443 | ALLOW | ✓ |
| 7 | github.com | 80 | DENY | ✓ |
| 8 | evil.example.com | 443 | DENY | ✓ |
| 9 | Red | 8888 | ALLOW | ✓ |
| 10 | 10.0.0.1 | 80 | DENY | ✓ |

## Acceptance criterion met
"matrix of allowed/blocked probes with raw logs" — 10-case matrix executed, all correct, audit log at `memory/ops/egress-audit.jsonl`.

## Remaining for full closure
- Wire into sandbox network layer (currently advisory; actual blocking still via netcmd firewall)
- Add per-agent policy scoping (e.g. Researcher gets more domains than Builder)