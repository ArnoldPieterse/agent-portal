# Security Scan Report
Generated: 2026-11-19 16:37 UTC
Files scanned: 97
**Verdict: FAIL (40 issues)**

Total findings: 40

## Hardcoded Secrets (4)
- **pale_dl.py:2** — Hardcoded bearer token
  ```
  H = {'Authorization': 'Bearer sk-unsloth-f3c04f0ea9784dd512534cafdb5efc34', 'Con
  ```
- **memory/verifier/_security_fixture_vulnerable.py:7** — Hardcoded credential assignment
  ```
  api_key = "sk_live_abc123def456ghi789"
  ```
- **memory/verifier/_security_fixture_vulnerable.py:9** — Hardcoded credential assignment
  ```
  auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.faketokenvalue"
  ```
- **memory/verifier/_security_fixture_vulnerable.py:10** — AWS Access Key ID
  ```
  aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
  ```

## SQL Injection Vectors (5)
- **memory/verifier/evolution_lifecycle_validator.py:85** — f-string SQL injection vector
  ```
  raise ValueError(f"select illegal: {eid} is {st}, not TEST_PASSED")
  ```
- **memory/verifier/security_scan.py:44** — .format() SQL injection vector
  ```
  (r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\b.*\.format\(", ".format() SQL injection 
  ```
- **memory/verifier/security_scan.py:245** — f-string SQL injection vector
  ```
  lines.insert(3, f"**Verdict: {verdict}**")
  ```
- **memory/verifier/_security_fixture_vulnerable.py:16** — f-string SQL injection vector
  ```
  query = f"SELECT * FROM users WHERE username = '{name}'"
  ```
- **memory/verifier/_security_fixture_vulnerable.py:28** — .format() SQL injection vector
  ```
  sql = "UPDATE users SET status = '{}' WHERE id = {}".format(status, uid)
  ```

## XSS Vectors (JS) (24)
- **ui/components.js:22** — innerHTML from dynamic variable (XSS risk)
  ```
  if (html != null) e.innerHTML = html;
  ```
- **ui/components.js:59** — innerHTML from dynamic variable (XSS risk)
  ```
  if (opts.bodyHtml) body.innerHTML = opts.bodyHtml;
  ```
- **ui/components.js:198** — innerHTML from dynamic variable (XSS risk)
  ```
  if (typeof opts.body === "string") body.innerHTML = opts.body;
  ```
- **ui/core.js:193** — innerHTML from dynamic variable (XSS risk)
  ```
  chip.innerHTML=UI.icon("wrench")+" "+esc(tn); toolRow.appendChild(chip); }
  ```
- **ui/core.js:370** — innerHTML from dynamic variable (XSS risk)
  ```
  $("fleetBody").innerHTML=html||UI.emptyState({icon:"agent",title:"No hosts repor
  ```
- **ui/core.js:411** — innerHTML from dynamic variable (XSS risk)
  ```
  el.innerHTML=evs.map(e=>'<div style="margin:2px 0">'+esc(e.ts.slice(5))+' · <b>'
  ```
- **ui/core.js:452** — innerHTML from dynamic variable (XSS risk)
  ```
  el.innerHTML=h; }
  ```
- **ui/core.js:456** — innerHTML from dynamic variable (XSS risk)
  ```
  b.innerHTML=ic+' Print';
  ```
- **ui/core.js:460** — innerHTML from dynamic variable (XSS risk)
  ```
  if($("fleetBody"))$("fleetBody").innerHTML=UI.skeleton(4,18);
  ```
- **ui/core.js:461** — innerHTML from dynamic variable (XSS risk)
  ```
  if($("goalsBody"))$("goalsBody").innerHTML=UI.skeleton(3,52);
  ```
- **ui/core.js:495** — innerHTML from dynamic variable (XSS risk)
  ```
  $("fleetBody").innerHTML=UI.emptyState({icon:"agent",title:"No hosts reporting",
  ```
- **ui/core.js:496** — innerHTML from dynamic variable (XSS risk)
  ```
  $("goalsBody").innerHTML=UI.emptyState({icon:"goal",title:"No goals set",msg:"Go
  ```
- **ui/core.js:497** — innerHTML from dynamic variable (XSS risk)
  ```
  const fl=$("filesList"); if(fl){fl.innerHTML=""; const li=UI.el("li"); li.innerH
  ```
- **ui/fleet_health.js:117** — innerHTML from dynamic variable (XSS risk)
  ```
  container.innerHTML = h;
  ```
- **ui/fleet_status.js:36** — innerHTML from dynamic variable (XSS risk)
  ```
  el.innerHTML = html;
  ```
- **ui/fleet_topology.js:108** — innerHTML from dynamic variable (XSS risk)
  ```
  svg.innerHTML = nodes.map(portalNode).join("") + nodes.map(svgNode).join("");
  ```
- **ui/fleet_topology.js:111** — innerHTML from dynamic variable (XSS risk)
  ```
  g.addEventListener("mouseenter", function(e){ tip.innerHTML=tooltipHTML(h); tip.
  ```
- **ui/fleet_topology.js:114** — innerHTML from dynamic variable (XSS risk)
  ```
  g.addEventListener("click", function(){ det.innerHTML=detailHTML(h); det.hidden=
  ```
- **ui/fleet_topology.js:115** — innerHTML from dynamic variable (XSS risk)
  ```
  g.addEventListener("keydown", function(e){ if(e.key==="Enter"||e.key===" "){ e.p
  ```
- **ui/notifications.js:12** — innerHTML from dynamic variable (XSS risk)
  ```
  b.innerHTML=ic+'<span class="notif-badge hidden" id="notifBadge">0</span>';
  ```
- **ui/notifications.js:27** — innerHTML from dynamic variable (XSS risk)
  ```
  const x=el("button","toast-close"); x.type="button"; x.setAttribute("aria-label"
  ```
- **ui/uploads.js:348** — innerHTML from dynamic variable (XSS risk)
  ```
  { const _gb=$("goalsBody"); if(_gb&&(typeof UI!=="undefined")&&!_gb.dataset.load
  ```
- **ui/uploads.js:366** — innerHTML from dynamic variable (XSS risk)
  ```
  $("goalsBody").innerHTML=html||((typeof UI!=="undefined")?UI.emptyState({icon:"g
  ```
- **ui/uploads.js:388** — innerHTML from dynamic variable (XSS risk)
  ```
  el.innerHTML=Object.entries(o.metrics).map(([k,v])=>'<div class="mh-card" style=
  ```

## File Permissions (0)
PASS — no issues found.

## CORS Configuration (7)
- **agent_portal.py:3963** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:3975** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:3989** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:4005** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:4055** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:4364** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
- **agent_portal.py:4479** — Wildcard CORS origin (*) — restrict to known origins
  ```
  self.send_header("Access-Control-Allow-Origin", "*")
  ```
