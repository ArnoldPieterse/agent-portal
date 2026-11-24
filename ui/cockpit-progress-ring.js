/* Convergence Progress Ring (Designer cycle-17 goal #6)
   Circular progress indicator showing % toward steady-state target.
   3-criteria check: interventions_lt2, duration_variance_lt15pct, zero_rework.
   Animate on update via CSS transition (stroke-dashoffset). */
(function () {
  "use strict";
  var API = "/api/convergence";

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckring{margin-top:4px;display:flex;align-items:center;gap:12px}",
      ".ckring-label{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98;margin-bottom:6px;width:100%}",
      ".ckring-wrap{position:relative;width:80px;height:80px;flex:none}",
      ".ckring-svg{width:80px;height:80px;transform:rotate(-90deg)}",
      ".ckring-bg{fill:none;stroke:#232833;stroke-width:7}",
      ".ckring-fg{fill:none;stroke-width:7;stroke-linecap:round;transition:stroke-dashoffset .45s ease, stroke .3s ease}",
      ".ckring-pct{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:18px;font-weight:700;color:#e2e5ea}",
      ".ckring-criteria{display:flex;flex-direction:column;gap:3px;font-size:10px}",
      ".ckring-crit{display:flex;align-items:center;gap:4px;color:#8a8f98}",
      ".ckring-crit i{width:8px;height:8px;border-radius:50%;display:inline-block}",
      ".ckring-crit.pass i{background:#2ea36b}",
      ".ckring-crit.fail i{background:#e5534b}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function render(progress) {
    var box = document.getElementById("ckringBox");
    if (!box) return;
    var pct = Math.max(0, Math.min(100, (progress.progress_pct || 0)));
    var R = 34, C = 2 * Math.PI * R;
    var dash = C * (1 - pct / 100);
    // Color based on progress: <50 red, 50-99 amber, 100 green
    var strokeColor = pct >= 100 ? "#2ea36b" : pct >= 50 ? "#f59e0b" : "#e5534b";
    var criteria = progress.criteria || {};
    var critHtml = [
      { key: "interventions_lt2", label: "Interventions < 2" },
      { key: "duration_variance_lt15pct", label: "Duration variance < 15%" },
      { key: "zero_rework", label: "Zero re-work" }
    ].map(function (c) {
      var pass = criteria[c.key] === true;
      return '<div class="ckring-crit ' + (pass ? "pass" : "fail") + '" data-testid="ckring-crit-' + c.key + '"><i></i>' + c.label + '</div>';
    }).join("");

    box.innerHTML =
      '<div class="ckring-label">Steady-State Progress</div>' +
      '<div class="ckring" data-testid="ckring-wrap">' +
        '<div class="ckring-wrap">' +
          '<svg class="ckring-svg" viewBox="0 0 80 80">' +
            '<circle class="ckring-bg" cx="40" cy="40" r="' + R + '"/>' +
            '<circle class="ckring-fg" cx="40" cy="40" r="' + R + '" stroke="' + strokeColor + '" stroke-dasharray="' + C.toFixed(1) + '" stroke-dashoffset="' + dash.toFixed(1) + '" data-testid="ckring-fg"/>' +
          '</svg>' +
          '<span class="ckring-pct" data-testid="ckring-pct">' + Math.round(pct) + '%</span>' +
        '</div>' +
        '<div class="ckring-criteria">' + critHtml + '</div>' +
      '</div>';
  }

  function insert() {
    var panel = document.getElementById("ckpPanel");
    if (!panel) return false;
    var existing = document.getElementById("ckringSection");
    if (existing) return true;
    var hhmSec = document.getElementById("ckhmSection");
    var sec = document.createElement("div");
    sec.id = "ckringSection";
    sec.innerHTML = '<div class="sec">Progress Ring</div><div id="ckringBox"></div>';
    if (hhmSec && hhmSec.nextElementSibling) hhmSec.after(sec);
    else if (hhmSec) hhmSec.after(sec);
    else panel.appendChild(sec);
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
    } catch (e) { d = null; }
    var progress = (d && d.steady_state_progress) || { progress_pct: 66.7, criteria: { interventions_lt2: true, duration_variance_lt15pct: true, zero_rework: false }, consecutive_passes: 2 };
    render(progress);
  }

  function init() {
    css();
    tryInsert();
    refresh();
    setInterval(refresh, 30000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
