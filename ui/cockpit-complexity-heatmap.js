/* Goal Complexity Heatmap (Designer cycle-17 goal #5)
   Grid view of current cycle goals colored by complexity score 1-5.
   Colors: 1=#2ea36b(light green) → 5=#9b1c1c(dark red).
   Tooltip shows scoring factors. Data from /api/convergence, falls back to mock. */
(function () {
  "use strict";
  var API = "/api/convergence";
  // Complexity scale: 1=light green → 5=dark red
  var SCALE = [
    { score: 1, color: "#2ea36b", label: "Light" },
    { score: 2, color: "#84cc16", label: "Moderate" },
    { score: 3, color: "#f59e0b", label: "Medium" },
    { score: 4, color: "#ef4444", label: "Heavy" },
    { score: 5, color: "#9b1c1c", label: "Critical" }
  ];

  // 10 mock goals for verification
  var MOCK = [
    { id: 1, title: "Convergence Dashboard", score: 4, factors: ["multi-widget", "API wiring"] },
    { id: 2, title: "Steady-State Indicator", score: 3, factors: ["CSS animation", "mode detection"] },
    { id: 3, title: "Cycle Forecast Widget", score: 4, factors: ["SVG chart", "prediction algo"] },
    { id: 4, title: "Intervention Timeline", score: 2, factors: ["single track", "color mapping"] },
    { id: 5, title: "Complexity Heatmap", score: 3, factors: ["grid layout", "tooltip system"] },
    { id: 6, title: "Progress Ring", score: 2, factors: ["conic-gradient", "animation"] },
    { id: 7, title: "Autonomy Cards", score: 4, factors: ["8 cards", "sortable", "data join"] },
    { id: 8, title: "Transition Animation", score: 3, factors: ["overlay", "timing"] },
    { id: 9, title: "Calm Mode", score: 2, factors: ["CSS class toggle"] },
    { id: 10, title: "Metrics Export", score: 4, factors: ["JSON download", "PNG generation"] }
  ];

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckhm{margin-top:4px}",
      ".ckhm-label{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98;margin-bottom:6px}",
      ".ckhm-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:4px}",
      ".ckhm-cell{border-radius:5px;padding:8px 6px;text-align:center;font-size:9px;color:#fff;line-height:1.3;position:relative;cursor:pointer;transition:transform .12s ease;min-height:40px;display:flex;align-items:center;justify-content:center}",
      ".ckhm-cell:hover{transform:scale(1.05);z-index:10}",
      ".ckhm-score{font-size:14px;font-weight:700;display:block}",
      ".ckhm-title{font-size:8px;opacity:.9;margin-top:2px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}",
      ".ckhm-tip{position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);background:#232833;color:#e2e5ea;font-size:9px;padding:4px 8px;border-radius:4px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .15s;z-index:20}",
      ".ckhm-cell:hover .ckhm-tip{opacity:1}",
      ".ckhm-scale{display:flex;gap:6px;margin-top:6px;font-size:9px;color:#8a8f98;align-items:center}",
      ".ckhm-scale i{width:10px;height:10px;border-radius:2px;display:inline-block}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function colorFor(score) {
    score = Math.max(1, Math.min(5, Math.round(score || 3)));
    return SCALE[score - 1].color;
  }

  function render(goals) {
    var box = document.getElementById("ckhmBox");
    if (!box) return;
    var cells = goals.map(function (g) {
      var c = colorFor(g.score);
      var factors = (g.factors || []).join(", ") || "n/a";
      var tip = '<span class="ckhm-tip">' + g.title + ' — ' + factors + '</span>';
      return '<div class="ckhm-cell" style="background:' + c + ';" data-testid="ckhm-cell-' + g.id + '" data-score="' + g.score + '">' +
        '<span class="ckhm-score">' + g.score + '</span>' +
        '<span class="ckhm-title">' + (g.title || "") + '</span>' + tip + '</div>';
    }).join("");
    var scale = SCALE.map(function (s) {
      return '<i style="background:' + s.color + '" title="' + s.score + ' = ' + s.label + '"></i>';
    }).join("");
    box.innerHTML =
      '<div class="ckhm-label">Goal Complexity — current cycle</div>' +
      '<div class="ckhm-grid" data-testid="ckhm-grid">' + cells + '</div>' +
      '<div class="ckhm-scale"><span>1</span>' + scale + '<span>5</span></div>';
  }

  function insert() {
    var panel = document.getElementById("ckpPanel");
    if (!panel) return false;
    var existing = document.getElementById("ckhmSection");
    if (existing) return true;
    var itlSec = document.getElementById("ckitlSection");
    var sec = document.createElement("div");
    sec.id = "ckhmSection";
    sec.innerHTML = '<div class="sec">Complexity Heatmap</div><div id="ckhmBox"></div>';
    if (itlSec && itlSec.nextElementSibling) itlSec.after(sec);
    else if (itlSec) itlSec.after(sec);
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
    var goals = MOCK;
    if (d && d.goal_complexity && Array.isArray(d.goal_complexity)) {
      goals = d.goal_complexity;
    }
    render(goals);
  }

  function init() {
    css();
    tryInsert();
    refresh();
    setInterval(refresh, 60000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
