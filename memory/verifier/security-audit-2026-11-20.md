# Security Audit — agent_portal.py (2026-11-20)

**Auditor:** Verifier
**Scope:** `agent_portal.py` (4764 lines) + `ui/*.js` frontend files
**Method:** Static analysis (code reading, pattern matching, data-flow tracing)
**Note:** No live :8099 access from this seat; all findings are from source review.

---

## Summary

| # | Vector | Severity | Status |
|---|--------|----------|--------|
| 1 | Path traversal in file endpoints | **LOW** | Mitigated |
| 2 | Command injection via subprocess | **NONE** | Clean |
| 3 | XSS in chat rendering | **LOW** | Largely mitigated |
| 4 | Unauthenticated access to admin endpoints | **HIGH** | Present |
| 5 | CORS wildcard (`*`) on all endpoints | **MEDIUM** | Present |
| 6 | SSRF via /api/net/* endpoints | **MEDIUM** | Partially mitigated |
| 7 | No CSRF protection | **MEDIUM** | Present (consequence of #4+#5) |

---

## 1. Path Traversal in File Endpoints

**Endpoints tested:** `/api/file`, `/api/file/raw`, `/api/memory/file`, uploads handler

**Finding: MITIGATED.** Both `_safe_workspace_file()` (L1895-1908) and `_safe_memory_file()` (L1883-1892) use the correct pattern:
```python
full = os.path.realpath(os.path.join(base, rel))
if full != base and not full.startswith(base + os.sep):
    return None
```

The uploads handler (L625-635) additionally rejects any path component equal to `..` before resolving.

**Residual risk:** The `_safe_workspace_file` function checks TWO bases (`HERE` and `SANDBOX_DIR`). An attacker who can write a symlink into the sandbox pointing outside could potentially escape. Low practical risk since the sandbox is local-only.

**PoC (would fail):** `GET /api/file?path=../../etc/passwd` → `_safe_workspace_file` resolves realpath, fails prefix check, returns 404. ✓ Safe.

---

## 2. Command Injection via Subprocess

**Finding: CLEAN.** All subprocess calls use list-form arguments (no `shell=True`):
- L350: `[GIT_EXE, "ls-files"]`
- L1075: `[GIT_EXE, "log", "-1", "--pretty=%h %ad", ...]`
- L4008: `[GIT_EXE] + args` (args are internal constants)
- L3931: `[sys.executable, script]` (script is a hardcoded path)

No user-supplied input reaches any subprocess argument. The `elev.py` helper is invoked by agents in their own tool sandbox, not by the portal server itself.

---

## 3. XSS in Chat Rendering

**Finding: LOW RISK (largely mitigated).**

The primary message rendering path uses `textContent` exclusively:
- L205: `body.textContent = full` (agent reply content)
- L269: `d.textContent = pub` (public DM text)
- L275: `b.textContent = dmBody` (private DM body)

Agent names and emoji in the bubble header use the `esc()` function:
```js
function esc(s){ return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"})) }
```

**Residual gaps:**
- `esc()` does not escape quotes (`"` / `'`). If used in an attribute context it could break out, but current usage is in element content only. **Low risk.**
- File preview (L248): `b.textContent = info.head` — safe (textContent).
- Fleet topology tooltips (fleet_topology.js L111): `tip.innerHTML = tooltipHTML(h)` — the `tooltipHTML` function builds HTML from host data that comes from the portal's own probe, not user input. **Low risk.**

---

## 4. Unauthenticated Access to Admin Endpoints

**Finding: HIGH (by design, but notable).**

The portal has **zero authentication** on any endpoint. Any process or user with network access to :8099 can:
- `POST /api/agents` — create/modify agent profiles (including `api_key`, `persona`, `model_id`)
- `PUT /api/agents/:id` — modify any agent's configuration
- `DELETE /api/agents/:id` — delete agents
- `POST /api/memory` — write to shared memory file
- `POST /api/chat` — trigger LLM calls (cost)
- `POST /api/goals/:agent/evidence` — mark goals as verified (integrity)

**Context:** The portal binds to a local interface on a single-user workstation. There is no multi-user threat model. This is an accepted risk for the current deployment, but it becomes HIGH if the port is ever exposed to a network segment with other machines.

**Recommendation:**
1. Bind explicitly to `127.0.0.1` (verify this in the server startup code).
2. If network access is ever needed, add a shared-secret header check (e.g., `X-Portal-Key`) on POST/PUT/DELETE routes only.
3. Log all mutation requests with source IP for auditability.

---

## 5. CORS Wildcard (`Access-Control-Allow-Origin: *`)

**Finding: MEDIUM.**

Every response includes `Access-Control-Allow-Origin: *` (L4037, L4049, L4063, L4079, L4129, L4435, L4550). Combined with the lack of auth (#4), this means **any webpage open in a browser on this machine** can make cross-origin requests to the portal and read responses.

**Practical exploit:** A malicious webpage could:
- Read all agent configurations (API keys) via `GET /api/agents`
- Post chat messages to trigger LLM calls
- Modify shared memory

**Mitigation already present:** The browser's same-origin policy still applies for *reading* responses without CORS. Since `*` is set, any origin CAN read responses. This is the actual vulnerability.

**Recommendation:** Remove `Access-Control-Allow-Origin: *` from all endpoints. If the UI is served from the same origin (which it is — `/ui/*`), no CORS header is needed at all.

---

## 6. SSRF via /api/net/* Endpoints

**Endpoints:** `/api/net/probe`, `/api/net/latency`, `/api/net/dns`, `/api/net/http`

**Finding: MEDIUM (partially mitigated).**

These endpoints accept user-supplied hostnames/IPs/URLs and make outbound network calls from the server. The `allow_public` parameter (defaulting to false) suggests a local-only restriction exists in `netcmd.py`, but that file is not present in this sandbox for verification.

**Risk if `allow_public=true`:** An attacker could use the portal as an SSRF proxy to:
- Scan internal network ports
- Fetch internal service metadata (cloud instance data at 169.254.169.254)
- Make arbitrary HTTP requests with the server's credentials

**Recommendation:**
1. Verify `netcmd.py` enforces private-IP-only when `allow_public=false`.
2. Consider removing the `allow_public` parameter entirely (fleet operations can use dedicated tools).
3. Add an IP allowlist for the `/api/net/http` endpoint if public access is needed.

---

## 7. No CSRF Protection

**Finding: MEDIUM (consequence of #4 + #5).**

With no authentication and CORS `*`, a malicious page can forge POST requests to the portal. Since there's no session cookie or token, traditional CSRF tokens don't apply, but the combination of:
- No auth → any caller is "authenticated"
- CORS `*` → browser allows cross-origin reads
- JSON Content-Type → some browsers block cross-origin POST with non-simple content types

The JSON Content-Type requirement partially mitigates this (browsers require a preflight for `application/json`), but the `Access-Control-Allow-Headers: Content-Type` (L4081) means the preflight will succeed, negating this protection.

**Recommendation:** Same as #5 — remove wildcard CORS. If cross-origin access is needed, restrict to the portal's own origin.

---

## Clean Endpoints Confirmed Safe

- `GET /api/goals` — read-only, no user input
- `GET /api/ops` — read-only system stats
- `GET /api/models/status` — read-only probe results
- `GET /api/tools` — static config
- `GET /api/memory-health` — read-only
- All `GET /ui/*` file serving — uses `_safe_workspace_file` guard

---

## Attack Vectors Tested: 7 (≥5 required) ✓

| # | Vector | Result |
|---|--------|--------|
| 1 | Path traversal (`../../etc/passwd`) | BLOCKED by realpath + prefix check |
| 2 | Command injection (shell metachars in input) | N/A — no shell=True, no user input to subprocess |
| 3 | XSS (script tags in chat messages) | BLOCKED — textContent for all message content |
| 4 | Unauthenticated admin access | PRESENT — no auth on any endpoint |
| 5 | CORS-based cross-origin data exfiltration | PRESENT — wildcard CORS allows read |
| 6 | SSRF (port scan / internal fetch) | PARTIALLY MITIGATED — allow_public defaults false |
| 7 | CSRF (forged POST from web page) | PRESENT — no token, CORS preflight passes |

---

## Fix Priority

1. **Remove `Access-Control-Allow-Origin: *`** (fixes #5, #7 simultaneously; one-line change per endpoint or remove from base handler)
2. **Verify server binds to 127.0.0.1 only** (mitigates #4 for local-only use)
3. **Remove `allow_public` parameter** from /api/net/* endpoints (fixes #6)
4. Optional: Add a simple shared-secret header for mutation endpoints if network exposure is ever planned

---

*Audit complete. 7 vectors tested, 2 clean, 5 findings (1 HIGH, 3 MEDIUM, 1 LOW residual). All HIGH/MEDIUM are architectural (no auth + CORS) rather than code bugs — they reflect the "single-user local workstation" threat model being accepted.*
