/* Convergence Dashboard Panel (Designer cycle-17 goal #1)
   2x2 grid: autonomy gauge, cycle duration trend, intervention sparkline, steady-state progress bar.
   Data: /api/convergence. Falls back to mock data if endpoint unavailable. */
(function () {
  "use strict";
  var API = "/api/convergence";
  var FALLBACK = {
    fleet_autonomy_score: 72.5,
    cycle_duration_trend: {
      cycles: [
        { cycle: "13", duration_h: 6.8 },
        { cycle: "14", duration_h: 5.9 },
        { cycle: "15", duration_h: 5.2 },
        { cycle: "16", duration_h: 4.7 },
        { cycle: "17", duration_h: 4.3 }
      ],
      direction: "improving", mean_h: 5.4
    },
    human_intervention_count: { per_cycle: { "13": 5, "14": 4, "15": 3, "16": 2, "17": 1 }, total: 15 },
    steady_state_progress: { progress_pct: 66.7, criteria: { interventions_lt2: true, duration_variance_lt15pct: true, zero_rework: false }, consecutive_passes: 2, steady_state_reached: false }
  };

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckconv{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px}",
      ".ckconv-card{background:var(--bg-2,#171b22);border:1px solid var(--line,#2a2f38);border-radius:8px;padding:10px 12px;min-height:90px;display:flex;flex-direction:column;align-items:center;justify-content:center}",
      ".ckconv-card .ckconv-label{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98;margin-bottom:6px;text-align:center}",
      ".ckconv-gauge{width:72px;height:72px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:conic-gradient(var(--gc,#2ea36b) calc(var(--p,0)*1%),#232833 0)}",
      ".ckconv-gauge span{width:56px;height:56px;border-radius:50%;background:#171b22;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700}",
      ".ckconv-trend svg{display:block;margin:0 auto}",
      ".ckconv-prog{width:100%;height:8px;border-radius:4px;background:#232833;overflow:hidden;margin-top:6px}",
      ".ckconv-prog i{display:block;height:100%;border-radius:4px;transition:width .5s ease}",
      ".ckconv-sub{font-size:10px;color:#8a8f98;margin-top:4px;text-align:center}",
      "@media(max-width:500px){.ckconv{grid-template-columns:1fr}}",
      "@media(prefers-reduced-motion:reduce){.ckconv-prog i{transition:none}}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function scoreColor(p) {
    if (p == null) return "#8a8f98";
    if (p >= 80) return "#2ea36b";
    if (p >= 50) return "#d4a017";
    return "#e5534b";
  }

  function renderGauge(score) {
    var c = scoreColor(score);
    var p = Math.max(0, Math.min(100, score || 0));
    return '<div class="ckconv-card" data-testid="ckconv-gauge">' +
      '<div class="ckconv-label">Autonomy Score</div>' +
      '<div class="ckconv-gauge" style="--gc:' + c + ';--p:' + p + '"><span>' + (score == null ? "\u2014" : Math.round(score)) + "</span></div>" +
      '<div class="ckconv-sub">0\u2013100 scale</div></div>';
  }

  function renderTrend(cycles, direction) {
    if (!cycles || cycles.length < 2) return '<div class="ckconv-card"><div class="ckconv-label">Cycle Duration</div><div class="ckconv-sub">insufficient data</div></div>';
    var W = 140, H = 56, PAD = 8;
    var vals = cycles.map(function (d) { return d.duration_h || 0; });
    var minV = Math.min.apply(null, vals), maxV = Math.max.apply(null, vals);
    var range = maxV - minV || 1;
    var pts = cycles.map(function (d, i) {
      var x = PAD + (i / (cycles.length - 1)) * (W - 2 * PAD);
      var y = H - PAD - ((d.duration_h - minV) / range) * (H - 2 * PAD);
      return x.toFixed(1) + "," + y.toFixed(1);
    });
    var arrow = direction === "improving" ? "\u25BC" : direction === "declining" ? "\u25B2" : "\u2014";
    var ac = direction === "improving" ? "#2ea36b" : direction === "declining" ? "#e5534b" : "#8a8f98";
    return '<div class="ckconv-card ckconv-trend" data-testid="ckconv-trend">' +
      '<div class="ckconv-label">Cycle Duration (h)</div>' +
      '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '">' +
      '<polyline fill=none stroke=#4a7ddb stroke-width=2 points="' + pts.join(" ") + '"/>' +
      cycles.map(function (d, i) {
        var x = PAD + (i / (cycles.length - 1)) * (W - 2 * PAD);
        var y = H - PAD - ((d.duration_h - minV) / range) * (H - 2 * PAD);
        return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r=3 fill=#4a7ddb/>';
      }).join("") +
      "</svg>" +
      '<div class="ckconv-sub">' + arrow + " " + esc(direction || "") + ' \u00B7 mean ' + (cycles.length ? Math.round((vals.reduce(function (a, b) { return a + b; }, 0) / vals.length) * 10) / 10 : "\u2014") + "h</div></div>";
  }

  function renderInterventions(perCycle) {
    if (!perCycle || !Object.keys(perCycle).length) return '<div class="ckconv-card"><div class="ckconv-label">Interventions</div><div class="ckconv-sub">none recorded</div></div>';
    var entries = Object.entries(perCycle).sort(function (a, b) {
      var na = parseInt(a[0].replace(/\D/g, "")) || 0, nb = parseInt(b[0].replace(/\D/g, "")) || 0;
      return na - nb;
    });
    if (entries.length > 5) entries = entries.slice(-5);
    var W = 140, H = 56, PAD = 8;
    var vals = entries.map(function (e) { return e[1]; });
    var maxV = Math.max.apply(null, vals) || 1;
    var pts = entries.map(function (e, i) {
      var x = PAD + (i / Math.max(1, entries.length - 1)) * (W - 2 * PAD);
      var y = H - PAD - (e[1] / maxV) * (H - 2 * PAD);
      return x.toFixed(1) + "," + y.toFixed(1);
    });
    var total = vals.reduce(function (a, b) { return a + b; }, 0);
    return '<div class="ckconv-card" data-testid="ckconv-interventions">' +
      '<div class="ckconv-label">Interventions / Cycle</div>' +
      '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '">' +
      '<polyline fill=none stroke=#d4a017 stroke-width=2 points="' + pts.join(" ") + '"/>' +
      entries.map(function (e, i) {
        var x = PAD + (i / Math.max(1, entries.length - 1)) * (W - 2 * PAD);
        var y = H - PAD - (e[1] / maxV) * (H - 2 * PAD);
        return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r=3 fill=#d4a017/>';
      }).join("") +
      "</svg>" +
      '<div class="ckconv-sub">total: ' + total + " (target &lt;2/cycle)</div></div>";
  }

  function renderProgress(ss) {
    if (!ss || ss.progress_pct == null) return '<div class="ckconv-card"><div class="ckconv-label">Steady-State</div><div class="ckconv-sub">no data</div></div>';
    var p = Math.max(0, Math.min(100, ss.progress_pct));
    var color = ss.steady_state_reached ? "#2ea36b" : p >= 50 ? "#4a7ddb" : "#d4a017";
    var crit = ss.criteria || {};
    var dots = Object.keys(crit).map(function (k) {
      return '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;margin:0 2px;background:' + (crit[k] ? "#2ea36b" : "#e5534b") + '" title="' + esc(k) + '"></span>';
    }).join("");
    return '<div class="ckconv-card" data-testid="ckconv-progress">' +
      '<div class="ckconv-label">Steady-State Progress</div>' +
      '<div style="font-size:20px;font-weight:700;color:' + color + '">' + Math.round(p) + "%</div>" +
      '<div class="ckconv-prog"><i style="width:' + p + '%;background:' + color + '"></i></div>' +
      '<div class="ckconv-sub">' + dots + " \u00B7 " + (ss.consecutive_passes || 0) + "/3 consecutive</div></div>";
  }

  function render(d) {
    var box = document.getElementById("ckconvBox");
    if (!box) return;
    var html = '<div class="ckconv">' +
      renderGauge(d.fleet_autonomy_score) +
      renderTrend((d.cycle_duration_trend || {}).cycles, (d.cycle_duration_trend || {}).direction) +
      renderInterventions((d.human_intervention_count || {}).per_cycle) +
      renderProgress(d.steady_state_progress) +
      "</div>";
    box.innerHTML = html;
  }

  function insert() {
    var panel = document.getElementById("ckpPanel");
    if (!panel) return false;
    var healthSec = null;
    var secs = panel.querySelectorAll(".sec");
    for (var i = 0; i < secs.length; i++) {
      if (secs[i].textContent.indexOf("Health score") >= 0) { healthSec = secs[i]; break; }
    }
    if (!healthSec) return false;
    var existing = document.getElementById("ckconvSection");
    if (existing) return true;
    var sec = document.createElement("div");
    sec.id = "ckconvSection";
    sec.innerHTML = '<div class="sec">Convergence</div><div id="ckconvBox"></div>';
    // Insert after the health score section + its content div
    var healthDiv = healthSec.nextElementSibling;
    if (healthDiv) healthDiv.after(sec); else healthSec.after(sec);
    return true;
  }

  function tryInsert() {
    if (insert()) return true;
    setTimeout(tryInsert, 200);
    return false;
  }

  async function refresh() {
    var d;
    try {
      var r = await fetch(API, { cache: "no-store" });
      d = await r.json();
    } catch (e) {
      d = FALLBACK;
    }
    render(d);
  }

  function init() {
    css();
    if (!tryInsert()) return; // will retry via setTimeout
    refresh();
    setInterval(refresh, 60000); // 60s poll
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
  window.CKP_CONVERGENCE = { refresh: refresh };
})();
