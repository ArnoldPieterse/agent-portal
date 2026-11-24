/* Agent Autonomy Comparison Cards (Designer cycle-17 goal #7)
   Per-agent cards: passes used, goals completed, re-work count, intervention count.
   Sortable by any metric. Data from /api/convergence; falls back to 8 mock agents. */
(function () {
  "use strict";
  var API = "/api/convergence";

  // 8 mock agents for verification
  var MOCK = [
    { agent: "Orchestrator", passes: 12, goals_completed: 8, rework: 1, interventions: 0 },
    { agent: "Researcher", passes: 9, goals_completed: 7, rework: 0, interventions: 1 },
    { agent: "Designer", passes: 11, goals_completed: 6, rework: 2, interventions: 1 },
    { agent: "Builder", passes: 8, goals_completed: 5, rework: 1, interventions: 0 },
    { agent: "Verifier", passes: 7, goals_completed: 6, rework: 0, interventions: 0 },
    { agent: "Archivist", passes: 6, goals_completed: 4, rework: 0, interventions: 1 },
    { agent: "Scribe", passes: 5, goals_completed: 3, rework: 1, interventions: 0 },
    { agent: "Mechanic", passes: 10, goals_completed: 7, rework: 0, interventions: 0 }
  ];

  var sortKey = "goals_completed";
  var sortDir = -1; // desc

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckcards{margin-top:4px}",
      ".ckcards-label{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center}",
      ".ckcards-sort{display:flex;gap:4px}",
      ".ckcards-sort button{font-size:9px;padding:2px 6px;border-radius:3px;border:1px solid #2a2f38;background:#171b22;color:#8a8f98;cursor:pointer}",
      ".ckcards-sort button.on{background:#2ea36b22;border-color:#2ea36b;color:#2ea36b}",
      ".ckcards-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}",
      ".ckcard{background:var(--bg-2,#171b22);border:1px solid var(--line,#2a2f38);border-radius:6px;padding:8px 10px;position:relative}",
      ".ckcard-name{font-size:10px;font-weight:600;color:#e2e5ea;margin-bottom:4px}",
      ".ckcard-metrics{display:grid;grid-template-columns:1fr 1fr;gap:2px}",
      ".ckcard-metric{font-size:9px;color:#8a8f98}",
      ".ckcard-metric b{color:#e2e5ea;font-size:11px;display:block}",
      ".ckcard-rank{position:absolute;top:6px;right:8px;font-size:9px;color:#5a5f68}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function render(agents) {
    var box = document.getElementById("ckcardsBox");
    if (!box) return;
    // Sort
    var sorted = agents.slice().sort(function (a, b) {
      return (a[sortKey] - b[sortKey]) * sortDir;
    });
    var cards = sorted.map(function (a, i) {
      return '<div class="ckcard" data-testid="ckcard-' + a.agent.toLowerCase() + '" data-agent="' + a.agent + '">' +
        '<span class="ckcard-rank">#' + (i + 1) + '</span>' +
        '<div class="ckcard-name">' + a.agent + '</div>' +
        '<div class="ckcard-metrics">' +
          '<div class="ckcard-metric"><b>' + a.passes + '</b>passes</div>' +
          '<div class="ckcard-metric"><b>' + a.goals_completed + '</b>goals</div>' +
          '<div class="ckcard-metric"><b>' + a.rework + '</b>re-work</div>' +
          '<div class="ckcard-metric"><b>' + a.interventions + '</b>interv.</div>' +
        '</div></div>';
    }).join("");
    // Sort buttons
    var keys = ["passes", "goals_completed", "rework", "interventions"];
    var btns = keys.map(function (k) {
      var active = k === sortKey ? " on" : "";
      return '<button class="ckcard-sortbtn' + active + '" data-key="' + k + '">' + k.replace("_", " ") + '</button>';
    }).join("");
    box.innerHTML =
      '<div class="ckcards-label">Autonomy by Agent <span class="ckcards-sort" data-testid="ckcards-sort">' + btns + '</span></div>' +
      '<div class="ckcards-grid" data-testid="ckcards-grid">' + cards + '</div>';
    // Wire sort buttons
    box.querySelectorAll(".ckcard-sortbtn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var k = this.getAttribute("data-key");
        if (sortKey === k) { sortDir *= -1; } else { sortKey = k; sortDir = -1; }
        render(currentData);
      });
    });
  }

  var currentData = MOCK;

  function insert() {
    var panel = document.getElementById("ckpPanel");
    if (!panel) return false;
    var existing = document.getElementById("ckcardsSection");
    if (existing) return true;
    var ringSec = document.getElementById("ckringSection");
    var sec = document.createElement("div");
    sec.id = "ckcardsSection";
    sec.innerHTML = '<div class="sec">Autonomy Cards</div><div id="ckcardsBox"></div>';
    if (ringSec && ringSec.nextElementSibling) ringSec.after(sec);
    else if (ringSec) ringSec.after(sec);
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
    if (d && d.agent_autonomy && Array.isArray(d.agent_autonomy)) {
      currentData = d.agent_autonomy;
    }
    render(currentData);
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
