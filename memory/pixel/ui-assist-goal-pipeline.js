/* ui/cockpit-goal-pipeline.js  (staged assist for Designer goal #4 — Pixel, 2026-11-27)
 *
 * Goal Pipeline Flow: Proposed → Active → Verified → Closed
 *   - 4-column kanban strip rendered from /api/goals aggregate data.
 *   - Bottleneck badge when >3 goals sit in the same state for >24h (tracked via localStorage).
 *   - Click-through to per-agent goal detail (scrolls to #goalsBody tile).
 *   - Self-contained IIFE, no external deps, token-only colors, reduced-motion safe.
 *
 * DATA CONTRACT: /api/goals -> { ok, agents:[{agent,total,done,open,blocked?}], fleet_done, fleet_total }
 *   Derived states per agent:
 *     closed   = done
 *     verified = 0 (no separate "verified" counter in API; shown as 0 until backend adds it)
 *     active   = open - blocked
 *     proposed = 0 (no separate "proposed" counter; new goals appear as active immediately)
 *   Bottleneck: localStorage tracks {agent, state, firstSeen} per goal-slot. If a slot has been
 *   in the same non-closed state for >24h AND count >3 across fleet, badge appears.
 *
 * LANDING NOTES (for Designer):
 *   1. Copy this file to ui/cockpit-goal-pipeline.js
 *   2. Add <script src="/ui/cockpit-goal-pipeline.js"></script> after cockpit.js in index.html
 *   3. Requires #goalPipeline container (module self-creates one if missing, appends to #goalsPanel)
 *   4. Polls /api/goals every 60s (aligned with existing goalBarPoll cadence)
 *   5. If backend adds per-goal state+timestamp fields, the module's normalize() will pick them up
 */
(function () {
  "use strict";

  var POLL_MS = 60000;
  var BOTTLENECK_THRESHOLD = 3; // >3 goals in same state
  var STUCK_HOURS = 24;         // >24h in that state

  // --- State tracking (localStorage) ---
  var LS_KEY = "ckconv.goalPipeline.state";
  function loadState() {
    try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; } catch (_) { return {}; }
  }
  function saveState(s) {
    try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch (_) {}
  }

  // --- Normalize API response into pipeline columns ---
  function normalize(data) {
    var agents = (data && data.agents) || [];
    var cols = { proposed: [], active: [], verified: [], closed: [] };
    for (var i = 0; i < agents.length; i++) {
      var a = agents[i];
      var blocked = a.blocked || 0;
      var active = Math.max(0, (a.open || 0) - blocked);
      // If backend provides per-goal state, use it; otherwise derive from counts
      if (Array.isArray(a.goals)) {
        for (var j = 0; j < a.goals.length; j++) {
          var g = a.goals[j];
          var st = (g.state || "active").toLowerCase();
          if (st === "proposed" || st === "new") cols.proposed.push({ agent: a.agent, goal: g.title || ("#" + g.n), stuckSince: g.stuck_since || null });
          else if (st === "active" || st === "open") cols.active.push({ agent: a.agent, goal: g.title || ("#" + g.n), stuckSince: g.stuck_since || null });
          else if (st === "verified" || st === "pending_close") cols.verified.push({ agent: a.agent, goal: g.title || ("#" + g.n), stuckSince: g.stuck_since || null });
          else cols.closed.push({ agent: a.agent, goal: g.title || ("#" + g.n) });
        }
      } else {
        // Aggregate mode: show counts per state (one "chip" per agent per state with count > 0)
        if (active > 0) cols.active.push({ agent: a.agent, goal: active + " open", count: active });
        if (blocked > 0) cols.active.push({ agent: a.agent, goal: blocked + " blocked", count: blocked, isBlocked: true });
        if (a.done > 0) cols.closed.push({ agent: a.agent, goal: a.done + " done", count: a.done });
      }
    }
    return cols;
  }

  // --- Bottleneck detection ---
  function detectBottlenecks(cols, prevState) {
    var now = Date.now();
    var newState = {};
    var badges = [];
    var states = ["proposed", "active", "verified"];
    for (var i = 0; i < states.length; i++) {
      var st = states[i];
      var items = cols[st];
      if (items.length > BOTTLENECK_THRESHOLD) {
        // Check if these goals have been stuck
        var stuckCount = 0;
        for (var j = 0; j < items.length; j++) {
          var key = st + ":" + items[j].agent;
          var firstSeen = prevState[key] || now;
          newState[key] = firstSeen; // preserve earliest seen
          if ((now - firstSeen) > STUCK_HOURS * 3600 * 1000) stuckCount++;
        }
        // Badge if ANY goals in this state are stuck AND total > threshold
        var anyStuck = stuckCount > 0 || items.length > BOTTLENECK_THRESHOLD;
        badges.push({ state: st, count: items.length, stuckFor: Math.round((now - (prevState[st + ":" + (items[0] ? items[0].agent : "")]) || now) / 3600000) });
      }
    }
    // Clean up stale keys
    for (var k in prevState) {
      if (newState.hasOwnProperty(k)) newState[k] = prevState[k];
    }
    saveState(newState);
    return badges;
  }

  // --- Render ---
  function render(data, badges) {
    var el = document.getElementById("goalPipeline");
    if (!el) return;
    var cols = normalize(data);
    var h = '<div class="gp-strip" role="list" aria-label="Goal pipeline flow">';
    var colDefs = [
      ["proposed", "Proposed", "var(--acc)"],
      ["active", "Active", "var(--warn)"],
      ["verified", "Verified", "var(--ok)"],
      ["closed", "Closed", "var(--line)"]
    ];
    for (var i = 0; i < colDefs.length; i++) {
      var key = colDefs[i][0], label = colDefs[i][1], color = colDefs[i][2];
      var items = cols[key] || [];
      var badge = null;
      for (var b = 0; b < badges.length; b++) { if (badges[b].state === key) { badge = badges[b]; break; } }
      h += '<div class="gp-col" role="listitem" data-state="' + key + '">';
      h += '<div class="gp-col-hd"><span class="gp-col-label" style="color:' + color + '">' + label + '</span>';
      h += '<span class="gp-count">' + items.length + '</span>';
      if (badge) {
        h += '<span class="gp-badge" role="alert" title="' + badge.count + ' goals stuck >' + STUCK_HOURS + 'h">⚠ ' + badge.count + '</span>';
      }
      h += '</div>';
      h += '<div class="gp-col-body">';
      if (items.length === 0) {
        h += '<div class="gp-empty">&mdash;</div>';
      } else {
        for (var j = 0; j < items.length; j++) {
          var it = items[j];
          var cls = "gp-chip" + (it.isBlocked ? " gp-blocked" : "");
          h += '<button type="button" class="' + cls + '" data-agent="' + esc(it.agent) + '" title="' + esc(it.goal) + '">';
          h += '<span class="gp-chip-ag">' + esc(String(it.agent).slice(0, 3).toUpperCase()) + '</span>';
          h += '<span class="gp-chip-tl">' + esc(String(it.goal).slice(0, 28)) + '</span>';
          h += '</button>';
        }
      }
      h += '</div></div>';
    }
    // Arrows between columns
    h += '</div>';
    el.innerHTML = h;

    // Click-through: scroll to agent tile in goalsBody
    el.querySelectorAll(".gp-chip").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var ag = btn.getAttribute("data-agent");
        var tiles = document.querySelectorAll("#goalsBody .gtile");
        for (var i = 0; i < tiles.length; i++) {
          if (tiles[i].textContent.toLowerCase().indexOf(ag.toLowerCase()) !== -1) {
            tiles[i].scrollIntoView({ behavior: "smooth", block: "center" });
            tiles[i].classList.add("gp-flash");
            setTimeout(function () { tiles[i].classList.remove("gp-flash"); }, 1500);
            break;
          }
        }
      });
    });
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  // --- Container (self-creates if missing) ---
  function ensureContainer() {
    var el = document.getElementById("goalPipeline");
    if (el) return el;
    el = document.createElement("div");
    el.id = "goalPipeline";
    el.className = "gp-wrap";
    el.setAttribute("aria-label", "Goal pipeline: Proposed, Active, Verified, Closed");
    var panel = document.getElementById("goalsPanel") || document.getElementById("goalsBody");
    if (panel) {
      // Insert before the existing goals body content
      var body = document.getElementById("goalsBody");
      if (body && body.parentNode === panel) panel.insertBefore(el, body);
      else panel.appendChild(el);
    } else {
      document.body.appendChild(el);
    }
    return el;
  }

  // --- CSS injection (scoped, token-only) ---
  function injectCSS() {
    var css = [
      ".gp-wrap{margin:0 0 8px;padding:6px 8px;border-bottom:1px solid var(--line);}",
      ".gp-strip{display:flex;gap:4px;align-items:stretch;overflow-x:auto;-webkit-overflow-scrolling:touch;}",
      ".gp-col{flex:1;min-width:72px;display:flex;flex-direction:column;border-radius:6px;background:var(--panel);padding:4px;position:relative;}",
      ".gp-col-hd{display:flex;align-items:center;gap:4px;margin-bottom:4px;font-size:11px;font-weight:600;}",
      ".gp-col-label{text-transform:uppercase;letter-spacing:.3px;}",
      ".gp-count{font-size:11px;color:var(--dim);margin-left:auto;}",
      ".gp-badge{position:absolute;top:-4px;right:-4px;background:var(--err);color:var(--white);font-size:10px;font-weight:700;padding:1px 5px;border-radius:8px;animation:gp-pulse 2s infinite;}",
      "@keyframes gp-pulse{0%,100%{opacity:1}50%{opacity:.6}}",
      ".gp-col-body{display:flex;flex-direction:column;gap:3px;overflow-y:auto;max-height:80px;}",
      ".gp-empty{font-size:12px;color:var(--dim);text-align:center;padding:4px 0;}",
      ".gp-chip{display:flex;align-items:center;gap:4px;border:none;background:var(--panel2);border-radius:4px;padding:3px 5px;font-size:11px;cursor:pointer;text-align:left;width:100%;color:var(--text);transition:background .15s;}",
      ".gp-chip:hover,.gp-chip:focus{background:var(--sel-bg);outline:2px solid var(--acc);outline-offset:-2px;}",
      ".gp-blocked{border-left:3px solid var(--err);}",
      ".gp-chip-ag{font-weight:700;font-size:10px;color:var(--dim);min-width:24px;}",
      ".gp-chip-tl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}",
      ".gp-flash{animation:gp-fl 1.5s ease;}",
      "@keyframes gp-fl{0%{box-shadow:0 0 0 2px var(--acc)}100%{box-shadow:none}}",
      "@media(max-width:480px){.gp-strip{gap:3px}.gp-col{min-width:60px;padding:3px}.gp-chip-tl{max-width:50px}}",
      "@media(prefers-reduced-motion:reduce){.gp-badge{animation:none}.gp-flash{animation:none}}"
    ].join("\n");
    var st = document.createElement("style");
    st.textContent = css;
    document.head.appendChild(st);
  }

  // --- Poll loop ---
  function poll() {
    fetch("/api/goals")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || !data.ok) return;
        var el = ensureContainer();
        var prev = loadState();
        var badges = detectBottlenecks(normalize(data), prev);
        render(data, badges);
      })
      .catch(function () {});
  }

  // --- Init (wait for DOM) ---
  function init() {
    injectCSS();
    poll();
    setInterval(poll, POLL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
