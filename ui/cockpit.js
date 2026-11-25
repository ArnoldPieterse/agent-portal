/* Fleet Cockpit (Builder cycle-11 goals 1-5): agent grid, host gauges, goal bar,
   health gauge + 7d sparkline, decision log viewer w/ filters+search, predicted risks. */
(function () {
  "use strict";
  var API = "/api/fleet/cockpit";
  var panel = null, btn = null, last = null, timer = null;
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function pctColor(p) { if (p == null) return "#8a8f98"; if (p > 90) return "#e5534b"; if (p > 70) return "#d4a017"; return "#2ea36b"; }
  function tempColor(t) { if (t == null) return "#8a8f98"; if (t > 80) return "#e5534b"; if (t > 70) return "#d4a017"; return "#2ea36b"; }
  function healthColor(s) { if (s == null) return "#8a8f98"; if (s > 70) return "#2ea36b"; if (s >= 40) return "#d4a017"; return "#e5534b"; }

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckp{position:fixed;top:0;right:-640px;width:620px;max-width:100vw;height:100vh;z-index:95;background:var(--bg-1,#101318);color:var(--fg-1,#e8eaed);border-left:1px solid var(--line,#2a2f38);transition:right .25s ease;overflow-y:auto;padding:14px 16px 40px;font-size:13px}",
      ".ckp.open{right:0}",
      ".ckp-mode-banner{display:flex;align-items:center;gap:8px;margin:0 0 12px;padding:8px 10px;border-radius:8px;font-size:12px;font-weight:600;letter-spacing:.4px;border:1px solid transparent}",
      ".ckp-mode-banner[hidden]{display:none}",
      ".ckp-mode-banner .ckp-mode-dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto}",
      ".ckp-mode-banner.mode-work{background:color-mix(in srgb,#2ea36b 14%,transparent);border-color:color-mix(in srgb,#2ea36b 45%,transparent);color:color-mix(in srgb,#2ea36b 80%,var(--fg-1,#e8eaed))}",
      ".ckp-mode-banner.mode-work .ckp-mode-dot{background:#2ea36b}",
      ".ckp-mode-banner.mode-maintenance{background:color-mix(in srgb,#d4a017 14%,transparent);border-color:color-mix(in srgb,#d4a017 45%,transparent);color:color-mix(in srgb,#d4a017 80%,var(--fg-1,#e8eaed))}",
      ".ckp-mode-banner.mode-maintenance .ckp-mode-dot{background:#d4a017}",
      ".ckp-mode-banner.mode-idle{background:color-mix(in srgb,#8a8f98 14%,transparent);border-color:color-mix(in srgb,#8a8f98 45%,transparent);color:color-mix(in srgb,#8a8f98 80%,var(--fg-1,#e8eaed))}",
      ".ckp-mode-banner.mode-idle .ckp-mode-dot{background:#8a8f98}",
      "@media(max-width:768px){.ckp{width:100vw}}",
      ".ckp h2{margin:2px 0 10px;font-size:15px;display:flex;justify-content:space-between;align-items:center}",
      ".ckp .sec{margin:14px 0 6px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8a8f98}",
      ".ckgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}",
      ".ckcard{background:var(--bg-2,#171b22);border:1px solid var(--line,#2a2f38);border-radius:8px;padding:8px 10px}",
      ".ckbar{height:6px;border-radius:3px;background:#232833;overflow:hidden;margin-top:5px}",
      ".ckbar i{display:block;height:100%}",
      ".ckrow{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid #1d222b;font-size:12px}",
      ".ckdec{border:1px solid var(--line,#2a2f38);border-radius:6px;margin-bottom:6px;background:var(--bg-2,#171b22)}",
      ".ckdec .hd{padding:6px 9px;cursor:pointer;display:flex;gap:8px;align-items:center;font-size:12px}",
      ".ckdec .bd{display:none;padding:0 9px 8px;font-size:11px;color:#aab2bf;white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace}",
      ".ckdec.open .bd{display:block}",
      ".ckdec input,.ckdec select,.ckp select,.ckp input[type=search]{background:#12151b;color:#e8eaed;border:1px solid #2a2f38;border-radius:5px;padding:4px 6px;font-size:12px}",
      ".ckfilters{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}",
      ".ckgauge{width:92px;height:92px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;background:conic-gradient(var(--gc,#2ea36b) calc(var(--p,0)*1%),#232833 0)}",
      ".ckgauge span{width:74px;height:74px;border-radius:50%;background:#171b22;display:flex;align-items:center;justify-content:center}",
      ".ckhealth{display:flex;gap:14px;align-items:center}",
      /* Power allocation (pie) */
      ".ckpw-v{border-radius:8px;padding:7px 10px;font-size:12px;margin-bottom:8px;border:1px solid transparent}",
      ".ckpw-v.healthy{background:color-mix(in srgb,#2ea36b 14%,transparent);border-color:color-mix(in srgb,#2ea36b 45%,transparent);color:color-mix(in srgb,#2ea36b 85%,var(--fg-1,#e8eaed))}",
      ".ckpw-v.revisit{background:color-mix(in srgb,#d4a017 14%,transparent);border-color:color-mix(in srgb,#d4a017 45%,transparent);color:color-mix(in srgb,#d4a017 85%,var(--fg-1,#e8eaed))}",
      ".ckpw-v .rsn{display:block;font-weight:400;margin-top:3px;opacity:.92}",
      ".ckpw-body{display:flex;gap:14px;align-items:center;flex-wrap:wrap}",
      ".ckpw-legend{flex:1;min-width:220px}",
      ".ckpw-lrow{display:flex;align-items:center;gap:7px;padding:3px 0;border-bottom:1px solid #1d222b;font-size:12px}",
      ".ckpw-dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto}",
      ".ckpw-share{font-size:10px;color:#8a8f98;border:1px solid #2a2f38;border-radius:4px;padding:0 4px;white-space:nowrap}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function build() {
    if (panel) return;
    css();
    btn = document.createElement("button");
    btn.id = "ckpBtn";
    btn.textContent = "\u25A6 Cockpit";
    btn.title = "Fleet cockpit: agents, hosts, health, decisions, risks";
    btn.style.cssText = "margin-left:8px;padding:4px 10px;font-size:12px;cursor:pointer;background:#171b22;color:#e8eaed;border:1px solid #2a2f38;border-radius:6px";
    var hb = document.querySelector("header");
    if (hb) hb.appendChild(btn); else document.body.appendChild(btn);
    panel = document.createElement("div");
    panel.id = "ckpPanel";
    panel.className = "ckp";
    panel.innerHTML = "<h2>Fleet Cockpit <span style='font-weight:400;font-size:11px;color:#8a8f98'><span id=ckpStamp>loading\u2026</span></span></h2>" +
      "<div id=ckpModeBanner class=ckp-mode-banner hidden data-testid=cockpit-mode-banner></div>" +
      "<div class=sec>Agents</div><div id=ckpAgents class=ckgrid></div>" +
      "<div class=sec>Fleet goals</div><div id=ckpGoals></div>" +
      "<div class=sec>Host resources</div><div id=ckpHosts></div>" +
      "<div class=sec>Power allocation <span style='text-transform:none;letter-spacing:0'>(VRAM by agent)</span></div><div id=ckpPower></div>" +
      "<div class=sec>Health score</div><div id=ckpHealth class=ckhealth></div>" +
      "<div class=sec>Predicted risks</div><div id=ckpRisks></div>" +
      "<div class=sec>Recent decisions</div><div id=ckpDecs></div>";
    document.body.appendChild(panel);
    btn.onclick = function () { panel.classList.toggle("open"); if (panel.classList.contains("open") && !timer) start(); };
    document.addEventListener("click", function (e) {
      if (!panel || !panel.classList.contains("open")) return;
      if (panel.contains(e.target) || btn.contains(e.target)) return;
      panel.classList.remove("open");
    });
  }
  function bar(p, color) { return "<div class=ckbar><i style='width:" + Math.max(0, Math.min(100, p || 0)) + "%;background:" + color + "'></i></div>"; }

  function render(d) {
    var a = "";
    (d.agents || []).forEach(function (x) {
      var pct = x.total ? Math.round(100 * x.done / x.total) : 0;
      a += "<div class=ckcard><b>" + esc(x.agent) + "</b> <span style='float:right;color:#8a8f98'>" + (x.blocked ? "\u26A0" + x.blocked : "") + "</span>" +
        "<div style='font-size:12px;margin-top:3px'>" + x.done + " / " + x.total + " reached</div>" + bar(pct, pct >= 100 ? "#2ea36b" : "#4a7ddb") + "</div>";
    });
    document.getElementById("ckpAgents").innerHTML = a || "<i>no agents</i>";
    var g = d.goals || {};
    document.getElementById("ckpGoals").innerHTML = "<div class=ckrow><span>Fleet progress</span><b>" + (g.fleet_done != null ? g.fleet_done + " / " + g.fleet_total : "\u2014") + "</b></div>" +
      bar(g.fleet_pct, "#4a7ddb") + "<div style='font-size:11px;color:#8a8f98;margin-top:3px'>" + (g.fleet_pct != null ? Math.round(g.fleet_pct) + "% of current goal cycle" : "") + "</div>";
    var h = "";
    (d.hosts || []).forEach(function (x) {
      h += "<div class=ckrow><span style='min-width:70px'><b>" + esc(x.name) + "</b>" + (x.circuit ? " <span style=color:#e5534b>\u26A0" + esc(x.circuit.state) + "</span>" : "") + "</span>" +
        "<span>VRAM " + (x.vram_pct == null ? "\u2014" : x.vram_pct + "%") + bar(x.vram_pct, pctColor(x.vram_pct)) + "</span>" +
        "<span>CPU " + (x.cpu_pct == null ? "\u2014" : x.cpu_pct + "%") + bar(x.cpu_pct, pctColor(x.cpu_pct)) + "</span>" +
        "<span>" + (x.temp_c == null ? "" : x.temp_c + "\u00B0C ") + bar(x.temp_c, tempColor(x.temp_c)) + "</span></div>";
    });
    document.getElementById("ckpHosts").innerHTML = h || "<i>no hosts reported</i>";
    renderPower(d.power);

    var s = d.health_score, tr = d.health_trend || [];
    var prev = tr.length > 1 ? tr[tr.length - 2].score : null;
    var delta = (s != null && prev != null) ? (s - prev > 0 ? "\u25B2+" + (s - prev) : s - prev < 0 ? "\u25BC" + (s - prev) : "\u2014") : "";
    var gc = healthColor(s);
    var spark = "";
    if (tr.length >= 2) {
      var pts = tr.map(function (p, i) { return (i / (tr.length - 1) * 100).toFixed(1) + "," + (100 - Math.max(0, Math.min(100, p.score || 0))); });
      spark = "<svg width=120 height=36 style='margin-top:4px'><polyline fill=none stroke=" + gc + " stroke-width=2 points='" + pts.join(" ") + "'/></svg>";
    } else { spark = "<div style='font-size:11px;color:#8a8f98;margin-top:4px'>trend: awaiting more samples</div>"; }
    document.getElementById("ckpHealth").innerHTML =
      "<div class=ckgauge style='--gc:" + gc + ";--p:" + (s || 0) + "'><span>" + (s == null ? "\u2014" : s) + "</span></div>" +
      "<div><b>Health " + (s == null ? "\u2014" : s + "/100") + "</b> " + delta +
      "<div style='font-size:11px;color:#8a8f98'>green &gt;70 \u00B7 yellow 40\u201370 \u00B7 red &lt;40</div>" + spark + "</div>";
    var r = "";
    (d.predicted_risks || []).forEach(function (x) { r += "<div class=ckrow><span>" + esc(typeof x === "string" ? x : x.text || JSON.stringify(x)) + "</span></div>"; });
    document.getElementById("ckpRisks").innerHTML = r || "<i>none predicted</i>";
    renderDecs(d.recent_decisions || []);
  }

  var decState = { agent: "", type: "", outcome: "", q: "" };
  function renderDecs(list) {
    list = list.slice(-50).reverse();
    var box = document.getElementById("ckpDecs");
    if (!box.dataset.built) {
      box.innerHTML = "<div class=ckfilters>" +
        "<select id=ckpFA><option value=''>all agents</option></select>" +
        "<select id=ckpFT><option value=''>all types</option></select>" +
        "<select id=ckpFO><option value=''>all outcomes</option></select>" +
        "<input id=ckpFQ type=search placeholder='search decisions\u2026' style='flex:1;min-width:120px'></div><div id=ckpDecList></div>";
      box.dataset.built = "1";
      ["A", "T", "O"].forEach(function (k) {
        var sel = document.getElementById("ckpF" + k), key = k === "A" ? "agent" : k === "T" ? "type" : "outcome";
        var vals = {}; list.forEach(function (x) { if (x[key]) vals[x[key]] = 1; });
        Object.keys(vals).sort().forEach(function (v) { var o = document.createElement("option"); o.value = v; o.textContent = v; sel.appendChild(o); });
        sel.onchange = function () { decState[key] = sel.value; paintDecs(list); };
      });
      document.getElementById("ckpFQ").oninput = function (e) { decState.q = e.target.value.toLowerCase(); paintDecs(list); };
    }
    paintDecs(list);
  }
  function paintDecs(list) {
    var out = "";
    list.forEach(function (x, i) {
      var hay = JSON.stringify(x).toLowerCase();
      if (decState.agent && x.agent !== decState.agent) return;
      if (decState.type && x.type !== decState.type) return;
      if (decState.outcome && x.outcome !== decState.outcome) return;
      if (decState.q && hay.indexOf(decState.q) < 0) return;
      var head = [x.ts || x.time, x.agent, x.type, x.outcome].filter(Boolean).map(esc).join(" \u00B7 ") || esc(JSON.stringify(x).slice(0, 80));
      out += "<div class=ckdec id=ckd" + i + "><div class=hd onclick=document.getElementById('ckd" + i + "').classList.toggle('open')><span>" + head + "</span></div><div class=bd>" + esc(JSON.stringify(x, null, 1)) + "</div></div>";
    });
    document.getElementById("ckpDecList").innerHTML = out || "<i style='color:#8a8f98'>no decisions match</i>";
  }

  /* ---- Power allocation pie (VRAM committed to each agent's model seat) ---- */
  var PW_FALLBACK = ["#4f8cff", "#ff6b6b", "#2ea36b", "#d4a017", "#9b59b6", "#16a085",
                     "#e17055", "#00d2d3", "#c44569", "#f1c40f", "#7ed6df", "#636e72"];
  function pwArc(cx, cy, r0, r1, a0, a1) {
    var large = (a1 - a0) > Math.PI ? 1 : 0;
    function pt(r, a) { return (cx + r * Math.cos(a)).toFixed(2) + " " + (cy + r * Math.sin(a)).toFixed(2); }
    return "M" + pt(r1, a0) + " A" + r1 + " " + r1 + " 0 " + large + " 1 " + pt(r1, a1) +
           " L" + pt(r0, a1) + " A" + r0 + " " + r0 + " 0 " + large + " 0 " + pt(r0, a0) + " Z";
  }
  function renderPower(p) {
    var box = document.getElementById("ckpPower");
    if (!box) return;
    if (!p || !p.agents || !p.agents.length) { box.innerHTML = "<i style='color:#8a8f98'>no power data</i>"; return; }
    var v = p.verdict || {};
    var vh = "<div class=\"ckpw-v " + (v.level === "revisit" ? "revisit" : "healthy") + "\">" +
      (v.level === "revisit" ? "\u26A0 Revisit power allocation" : "\u2713 Power allocation healthy") +
      (p.pct_used != null ? " \u00b7 " + p.pct_used + "% of fleet VRAM committed (" + p.allocated_gb + " / " + p.capacity_gb + " GB)" : "") +
      (v.reasons || []).map(function (r) { return "<span class=rsn>\u00b7 " + esc(r) + "</span>"; }).join("") +
      "</div>";
    var slices = p.agents.filter(function (x) { return x.power_gb > 0; });
    var total = slices.reduce(function (s, x) { return s + x.power_gb; }, 0);
    var svg = "", a = -Math.PI / 2, cx = 85, cy = 85, R1 = 78, R0 = 47;
    if (slices.length === 1) {
      svg += "<circle cx=" + cx + " cy=" + cy + " r=" + R1 + " fill='" + (slices[0].color || PW_FALLBACK[0]) + "'/>" +
             "<circle cx=" + cx + " cy=" + cy + " r=" + R0 + " fill='#171b22'/>";
    } else {
      slices.forEach(function (x, i) {
        var a1 = a + (x.power_gb / total) * Math.PI * 2;
        svg += "<path d='" + pwArc(cx, cy, R0, R1, a, a1 - 0.004) + "' fill='" + (x.color || PW_FALLBACK[i % PW_FALLBACK.length]) +
               "'><title>" + esc(x.name) + ": " + x.power_gb + " GB (" + x.pct + "%) on " + esc(x.host) + "</title></path>";
        a = a1;
      });
    }
    svg = "<svg width=170 height=170 viewBox='0 0 170 170'>" + svg +
      "<text x=" + cx + " y=" + (cy - 3) + " text-anchor=middle fill=#e8eaed font-size=20 font-weight=700>" +
      (p.pct_used != null ? p.pct_used : "\u2014") + "%</text>" +
      "<text x=" + cx + " y=" + (cy + 15) + " text-anchor=middle fill=#8a8f98 font-size=9.5>of " + p.capacity_gb + " GB VRAM</text></svg>";
    var lg = slices.map(function (x, i) {
      var shared = x.shared_with && x.shared_with.length ?
        "<span class=ckpw-share title='shared seat: " + esc(x.shared_with.join(", ")) + "'>&#247;" + (x.shared_with.length + 1) + "</span>" : "";
      return "<div class=ckpw-lrow><span class=ckpw-dot style='background:" + (x.color || PW_FALLBACK[i % PW_FALLBACK.length]) + "'></span>" +
        "<span style='flex:1;min-width:0'><b>" + esc(x.name) + "</b> <span style='color:#8a8f98'>" + esc(x.model) + " \u00b7 " + esc(x.host) + (x.gpu_ids && x.gpu_ids.length ? " GPU" + x.gpu_ids.join(",") : "") + "</span></span>" +
        shared + "<b style='white-space:nowrap'>" + x.power_gb + " GB</b><span style='color:#8a8f98;white-space:nowrap;width:42px;text-align:right'>" + x.pct + "%</span></div>";
    }).join("");
    var hh = (p.hosts || []).map(function (x) {
      return "<div class=ckrow><span style='min-width:56px'><b>" + esc(x.name) + "</b></span>" +
        "<span style='flex:1'>" + bar(x.pct, pctColor(x.pct)) + " <span style='font-size:11px;color:#8a8f98'>" + x.allocated_gb + "/" + x.capacity_gb + " GB</span></span></div>";
    }).join("");
    box.innerHTML = vh + "<div class=ckpw-body><div>" + svg + "</div><div class=ckpw-legend>" + lg + hh + "</div></div>" +
      "<div style='font-size:10.5px;color:#8a8f98;margin-top:6px'>power = seat VRAM, split evenly across agents sharing a seat \u00b7 " + esc(p.unit || "") + "</div>";
  }

  function relTime(iso) {
    try {
      var ms = Date.now() - new Date(iso).getTime();
      if (isNaN(ms)) return "";
      var m = Math.round(ms / 60000);
      if (m < 1) return "just now";
      if (m < 60) return m + "m ago";
      var h = Math.round(m / 60);
      if (h < 24) return h + "h ago";
      return Math.round(h / 24) + "d ago";
    } catch (e) { return ""; }
  }
  function updateBanner(d) {
    var b = document.getElementById("ckpModeBanner");
    if (!b) return;
    var mode = d && d.fleet_mode ? String(d.fleet_mode).toUpperCase() : "";
    if (!mode) { b.hidden = true; return; }
    var cls = mode === "WORK" ? "mode-work" : (mode === "MAINTENANCE" ? "mode-maintenance" : (mode === "IDLE" ? "mode-idle" : "mode-idle"));
    var t = d.last_activity ? relTime(d.last_activity) : "";
    b.className = "ckp-mode-banner " + cls;
    b.hidden = false;
    b.innerHTML = "<span class=ckp-mode-dot></span>" + esc(mode) + (t ? " <span style='opacity:.75;font-weight:400'>\u00b7 " + esc(t) + "</span>" : "");
  }
  async function refresh() {
    try {
      var r = await fetch(API, { cache: "no-store" });
      last = await r.json();
      render(last);
      updateBanner(last);
      document.getElementById("ckpStamp").textContent = "updated " + new Date().toLocaleTimeString();
    } catch (e) {
      window.__CKP_ERR = e;   // debug hook: surface swallowed render errors to the console
      if (window.console && console.error) console.error("[cockpit]", e);
      document.getElementById("ckpStamp").textContent = "refresh failed";
    }
  }
  function start() { if (!timer) timer = setInterval(refresh, 30000); }
  function init() {
    build();
    refresh();
    start();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
  window.CKPIT = { refresh: refresh, data: function () { return last; } };
})();
