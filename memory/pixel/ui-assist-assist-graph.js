/* ui-assist-assist-graph.js - Designer Goal #3 assist (Pixel, 2026-11-27)
   Cross-Lane Assist Graph: SVG graph of who helped whom this cycle; edge thickness = assist
   count; every agent with >=1 assist appears; legend present.
   Data contract: records shaped like memory/scribe/assist-attribution.jsonl ->
     { cycle, goal, owner, assists:[names], credit_line }
   The module fetches /api/assists (the intended delivery route for that log); until the route
   exists it renders a clear empty state. All graph math is pure + DOM-free so it is unit-testable.
   Self-contained IIFE; staged for landing in ui/ (append to cockpit.js; index.html is pinned).
   Colours from tokens.css vars with fallbacks - no hardcoded hex in inline style attrs. */
(function () {
  "use strict";
  var W = 560, H = 360, PAD = 46, R_NODE = 15;
  var W_MIN = 1.5, W_MAX = 7;   // stroke-width range mapped to assist count

  /* --- pure graph math (ported to Python for vector tests) --- */
  function buildGraph(records) {
    var gave = {}, received = {};
    var edgeMap = {};           // "from\u0001to" -> count
    function bump(o, k, n) { o[k] = (o[k] || 0) + (n || 1); }
    (records || []).forEach(function (rec) {
      if (!rec) return;
      var owner = rec.owner;
      var assists = Array.isArray(rec.assists) ? rec.assists : [];
      if (owner) { received[owner] = (received[owner] || 0) + assists.length; }
      assists.forEach(function (a) {
        if (!a) return;
        bump(gave, a, 1);
        if (owner && a !== owner) {           // cross-lane only: skip self-assist loops
          var key = a + "\u0001" + owner;
          edgeMap[key] = (edgeMap[key] || 0) + 1;
        }
      });
    });
    var nodeIds = {};
    Object.keys(gave).forEach(function (k) { nodeIds[k] = true; });
    Object.keys(received).forEach(function (k) { nodeIds[k] = true; });
    var nodes = Object.keys(nodeIds)
      .filter(function (id) { return (gave[id] || 0) > 0 || (received[id] || 0) > 0; })
      .sort()
      .map(function (id) { return { id: id, gave: gave[id] || 0, received: received[id] || 0 }; });
    var edges = Object.keys(edgeMap).map(function (key) {
      var p = key.split("\u0001");
      return { from: p[0], to: p[1], count: edgeMap[key] };
    }).sort(function (a, b) { return a.from === b.from ? (a.to === b.to ? 0 : (a.to < b.to ? -1 : 1)) : (a.from < b.from ? -1 : 1); });
    return { nodes: nodes, edges: edges };
  }

  // linear map count -> stroke width; single-value range collapses to mid-point
  function edgeWidth(count, minC, maxC, wMin, wMax) {
    wMin = (wMin == null) ? W_MIN : wMin;
    wMax = (wMax == null) ? W_MAX : wMax;
    if (maxC <= minC) return Math.round(((wMin + wMax) / 2) * 10) / 10;
    var t = (count - minC) / (maxC - minC);
    return Math.round((wMin + t * (wMax - wMin)) * 10) / 10;
  }

  // deterministic circular layout: sorted node order -> angle by index
  function layout(nodes, width, height, pad) {
    var cx = width / 2, cy = height / 2, R = Math.min(width, height) / 2 - pad;
    var pos = {};
    nodes.forEach(function (n, i) {
      var a = (i / Math.max(nodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.id] = { x: Math.round((cx + R * Math.cos(a)) * 10) / 10, y: Math.round((cy + R * Math.sin(a)) * 10) / 10 };
    });
    return pos;
  }

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  /* --- render: records -> HTML string (DOM-free, unit-testable) --- */
  function renderAssistGraph(records, opts) {
    opts = opts || {};
    var g = buildGraph(records);
    if (!g.nodes.length) {
      return '<div class="ag-empty" role="status">No assist data yet this cycle.</div>';
    }
    var counts = g.edges.map(function (e) { return e.count; });
    var minC = Math.min.apply(null, counts), maxC = Math.max.apply(null, counts);
    var pos = layout(g.nodes, W, H, PAD);

    var parts = [];
    parts.push('<svg class="ag-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Cross-lane assist graph: edge thickness equals number of assists">');
    // edges first (under nodes)
    g.edges.forEach(function (e) {
      var a = pos[e.from], b = pos[e.to];
      if (!a || !b) return;
      parts.push('<line x1="' + a.x + '" y1="' + a.y + '" x2="' + b.x + '" y2="' + b.y + '" class="ag-edge" stroke-width="' + edgeWidth(e.count, minC, maxC) + '" aria-label="' + esc(e.from) + ' assisted ' + esc(e.to) + ' ' + e.count + ' time' + (e.count === 1 ? '' : 's') + '"></line>');
    });
    // nodes
    g.nodes.forEach(function (n) {
      var p = pos[n.id];
      parts.push('<g class="ag-node" data-agent="' + esc(n.id) + '">');
      parts.push('<circle cx="' + p.x + '" cy="' + p.y + '" r="' + R_NODE + '" class="ag-dot"></circle>');
      parts.push('<text x="' + p.x + '" y="' + (p.y - R_NODE - 4) + '" class="ag-label" text-anchor="middle">' + esc(n.id) + '</text>');
      parts.push('</g>');
    });
    parts.push('</svg>');

    // legend
    var midW = edgeWidth((minC + maxC) / 2, minC, maxC);
    parts.push('<div class="ag-legend" role="note">');
    parts.push('<span class="ag-leg-line" style="border-top-width:' + W_MIN + 'px"></span><span>' + minC + ' assist' + (minC === 1 ? '' : 's') + '</span>');
    parts.push('<span class="ag-leg-line" style="border-top-width:' + midW + 'px"></span><span>' + Math.round((minC + maxC) / 2) + '</span>');
    parts.push('<span class="ag-leg-line" style="border-top-width:' + W_MAX + 'px"></span><span>' + maxC + ' assists</span>');
    parts.push('<span class="ag-leg-cap">edge thickness = assist count &middot; node = agent (gave/received &ge;1)</span>');
    parts.push('</div>');
    return '<div class="ag-wrap">' + parts.join('') + '</div>';
  }

  /* --- CSS (token-based, no hardcoded hex) --- */
  function injectStyle() {
    if (document.getElementById("ckconvAssistGraphStyle") || !document.head) return;
    var s = document.createElement("style");
    s.id = "ckconvAssistGraphStyle";
    s.textContent =
      ".ag-wrap{display:flex;flex-direction:column;gap:var(--sp-8,8px);max-width:560px;}" +
      ".ag-svg{width:100%;height:auto;background:var(--panel,#151a22);border:1px solid var(--line,#2a3342);border-radius:var(--br-md,8px);}" +
      ".ag-edge{stroke:var(--acc,#4f8cff);stroke-opacity:.5;stroke-linecap:round;}" +
      ".ag-dot{fill:var(--panel2,#1b2230);stroke:var(--acc,#4f8cff);stroke-width:2;}" +
      ".ag-label{fill:var(--text,#e8edf4);font-size:var(--fs-11,11px);}" +
      ".ag-legend{display:flex;align-items:center;gap:var(--sp-8,8px);flex-wrap:wrap;color:var(--dim,#9aa7b8);font-size:var(--fs-12,12px);}" +
      ".ag-leg-line{display:inline-block;width:34px;border-top-style:solid;border-top-color:var(--acc,#4f8cff);}" +
      ".ag-leg-cap{color:var(--muted,#8b93a7);margin-left:auto;}" +
      ".ag-empty{padding:var(--sp-24,24px);text-align:center;color:var(--dim,#9aa7b8);border:1px dashed var(--line,#2a3342);border-radius:var(--br-md,8px);}";
    document.head.appendChild(s);
  }

  function mount(html) {
    var host = document.getElementById("ckconvAssistGraph");
    if (!host) return;
    injectStyle();
    host.innerHTML = html;
  }

  function load() {
    try {
      fetch("/api/assists", { headers: { "Accept": "application/json" } })
        .then(function (r) { if (!r.ok) throw new Error("http " + r.status); return r.json(); })
        .then(function (data) {
          var records = Array.isArray(data) ? data : (data && Array.isArray(data.records) ? data.records : null);
          mount(renderAssistGraph(records));
        })
        .catch(function () { mount(renderAssistGraph([])); }); // 0 console errors; graceful empty state
    } catch (e) {}
  }

  function init() {
    if (!document.body) return;
    var host = document.getElementById("ckconvAssistGraph");
    if (!host) { host = document.createElement("div"); host.id = "ckconvAssistGraph"; document.body.appendChild(host); }
    load();
  }

  // expose pure API for tests / other modules (no-op if window undefined)
  try { window.CkAssistGraph = { buildGraph: buildGraph, edgeWidth: edgeWidth, layout: layout, renderAssistGraph: renderAssistGraph }; } catch (e) {}

  if (typeof document !== "undefined" && document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else if (typeof document !== "undefined") {
    init();
  }
})();
