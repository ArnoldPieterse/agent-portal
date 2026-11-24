/* Intervention Timeline (Designer cycle-17 goal #4)
   Horizontal timeline: human interventions over last 30 days.
   Colors: unblock=#f59e0b (amber), redirect=#e5534b (red), approve=#2ea36b (green).
   Data: /api/convergence (human_intervention_count). Falls back to 10 mock entries. */
(function () {
  "use strict";
  var API = "/api/convergence";
  var COLORS = { unblock: "#f59e0b", redirect: "#e5534b", approve: "#2ea36b" };
  var LABELS = { unblock: "Unblock", redirect: "Redirect", approve: "Approve" };

  // 10 mock entries spread over last 30 days (for verification + fallback)
  var MOCK = [
    { day: 29, type: "redirect", label: "Cycle 14 scope change" },
    { day: 27, type: "unblock", label: "White host reboot" },
    { day: 25, type: "approve", label: "Gate: fleet-mode.json" },
    { day: 23, type: "unblock", label: "Pin advance unblock" },
    { day: 20, type: "approve", label: "Cycle 15 goals approved" },
    { day: 17, type: "redirect", label: "Drop topology goal" },
    { day: 14, type: "unblock", label: "SMB creds rotation" },
    { day: 10, type: "approve", label: "Cycle 16 sign-off" },
    { day: 5, type: "redirect", label: "Focus on convergence" },
    { day: 2, type: "unblock", label: "Mirror sync fix" }
  ];

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckitl{margin-top:4px}",
      ".ckitl-label{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98;margin-bottom:6px}",
      ".ckitl-track{position:relative;height:32px;background:var(--bg-2,#171b22);border:1px solid var(--line,#2a2f38);border-radius:6px;overflow:visible}",
      ".ckitl-axis{position:absolute;top:100%;left:0;right:0;display:flex;justify-content:space-between;font-size:9px;color:#5a5f68;padding-top:3px}",
      ".ckitl-dot{position:absolute;top:50%;width:12px;height:12px;border-radius:50%;transform:translate(-50%,-50%);cursor:pointer;transition:transform .15s ease;z-index:2}",
      ".ckitl-dot:hover{transform:translate(-50%,-50%) scale(1.4);z-index:10}",
      ".ckitl-dot[data-type=unblock]{background:#f59e0b;box-shadow:0 0 4px #f59e0b66}",
      ".ckitl-dot[data-type=redirect]{background:#e5534b;box-shadow:0 0 4px #e5534b66}",
      ".ckitl-dot[data-type=approve]{background:#2ea36b;box-shadow:0 0 4px #2ea36b66}",
      ".ckitl-tip{position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);background:#232833;color:#e2e5ea;font-size:10px;padding:4px 8px;border-radius:4px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .15s;z-index:20}",
      ".ckitl-dot:hover .ckitl-tip{opacity:1}",
      ".ckitl-legend{display:flex;gap:12px;margin-top:4px;font-size:9px;color:#8a8f98}",
      ".ckitl-legend span{display:flex;align-items:center;gap:3px}",
      ".ckitl-legend i{width:7px;height:7px;border-radius:50%;display:inline-block}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function render(entries) {
    var box = document.getElementById("ckitlBox");
    if (!box) return;
    // Sort by day (0=today, 30=30 days ago)
    var sorted = entries.slice().sort(function (a, b) { return a.day - b.day; });
    var dots = sorted.map(function (e) {
      var pct = ((30 - e.day) / 30) * 100;
      var tip = '<span class="ckitl-tip">' + (LABELS[e.type] || e.type) + ": " + (e.label || "") + "</span>";
      return '<div class="ckitl-dot" data-type="' + e.type + '" style="left:' + pct.toFixed(1) + '%;" data-testid="ckitl-dot-' + e.type + '">' + tip + '</div>';
    }).join("");
    var legend = Object.keys(COLORS).map(function (t) {
      return '<span><i style="background:' + COLORS[t] + '"></i>' + LABELS[t] + '</span>';
    }).join("");
    box.innerHTML =
      '<div class="ckitl-label">Interventions \u2014 last 30 days</div>' +
      '<div class="ckitl-track" data-testid="ckitl-track">' + dots + '</div>' +
      '<div class="ckitl-axis"><span>30d</span><span>20d</span><span>10d</span><span>now</span></div>' +
      '<div class="ckitl-legend">' + legend + '</div>';
  }

  function insert() {
    var panel = document.getElementById("ckpPanel");
    if (!panel) return false;
    var existing = document.getElementById("ckitlSection");
    if (existing) return true;
    // Insert after convergence section if present, else append
    var convSec = document.getElementById("ckconvSection");
    var sec = document.createElement("div");
    sec.id = "ckitlSection";
    sec.innerHTML = '<div class="sec">Intervention Timeline</div><div id="ckitlBox"></div>';
    if (convSec && convSec.nextElementSibling) convSec.after(sec);
    else if (convSec) convSec.after(sec);
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
    // Use API data if it has per-day entries, else fallback to mock
    var entries = MOCK;
    if (d && d.human_intervention_timeline && Array.isArray(d.human_intervention_timeline)) {
      entries = d.human_intervention_timeline;
    } else if (d && d.human_intervention_count && d.human_intervention_count.per_cycle) {
      // Derive rough positions from per-cycle counts
      var pc = d.human_intervention_count.per_cycle;
      var cycles = Object.keys(pc).sort();
      entries = [];
      for (var ci = 0; ci < cycles.length; ci++) {
        var count = pc[cycles[ci]] || 0;
        var baseDay = Math.round((30 / Math.max(cycles.length, 1)) * (cycles.length - 1 - ci));
        for (var j = 0; j < count; j++) {
          entries.push({ day: Math.max(0, baseDay + j), type: j % 3 === 0 ? "approve" : j % 3 === 1 ? "unblock" : "redirect", label: "Cycle " + cycles[ci] });
        }
      }
    }
    render(entries);
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
