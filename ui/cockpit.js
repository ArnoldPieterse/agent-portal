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
      ".ckhealth{display:flex;gap:14px;align-items:center}"
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
