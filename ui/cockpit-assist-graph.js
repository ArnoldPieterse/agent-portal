/* Cross-Lane Assist Graph (Designer cycle-20 goal #2 - Pixel assist)
   SVG circular graph: nodes = agents, edges = assist relationships.
   Edge stroke-width proportional to assist count. Legend shows scale.
   Data: /api/assist-log (fallback: memory/ops/assist-log.json). */
(function () {
  "use strict";
  var API = "/api/assist-log";
  var FALLBACK = "memory/ops/assist-log.json";
  var SVG_NS = "http://www.w3.org/2000/svg";

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".ckassg{position:relative;width:100%;max-width:480px;margin:8px auto}",
      ".ckassg svg{display:block;width:100%;height:auto}",
      ".ckassg .node-label{font-size:9px;fill:var(--fg);text-anchor:middle;dominant-baseline:central;pointer-events:none}",
      ".ckassg .edge{stroke:var(--dim,rgba(255,255,255,.3));fill:none;opacity:.6}",
      ".ckassg .edge:hover{opacity:1;stroke:var(--ok,#4ecdc4)}",
      ".ckassg .node-circle{fill:var(--bg-2,var(--panel));stroke:var(--line);stroke-width:1.5;cursor:default}",
      ".ckassg .node-circle:hover{stroke:var(--ok,#4ecdc4)}",
      ".ckassg .legend{display:flex;align-items:center;gap:8px;margin-top:6px;font-size:10px;color:var(--dim);justify-content:center}",
      ".ckassg .legend-line{height:2px;width:32px;border-radius:1px;background:var(--dim)}",
      ".ckassg .empty-state{text-align:center;padding:24px 0;font-size:12px;color:var(--dim)}"
    ].join("\n");
    return s;
  }

  function render(container, data) {
    var nodes = data.nodes || [];
    var edges = data.edges || [];
    if (nodes.length < 2) {
      container.innerHTML = '<div class="empty-state" role="status">No assist data yet.</div>';
      return;
    }

    var size = 360, cx = size / 2, cy = size / 2, r = 130;
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + size + " " + size);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Cross-lane assist graph: " + nodes.length + " agents, " + edges.length + " relationships");

    // Compute max edge count for scaling
    var maxCount = 1;
    edges.forEach(function (e) { if (e.count > maxCount) maxCount = e.count; });

    // Node positions (circular layout)
    var nodePos = {};
    nodes.forEach(function (n, i) {
      var angle = (2 * Math.PI * i / nodes.length) - Math.PI / 2;
      nodePos[n] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
    });

    // Draw edges (curved paths between nodes)
    edges.forEach(function (e) {
      var p1 = nodePos[e.from], p2 = nodePos[e.to];
      if (!p1 || !p2) return;
      var midX = (p1.x + p2.x) / 2, midY = (p1.y + p2.y) / 2;
      // Offset control point toward center for a nice arc
      var cpx = cx + (midX - cx) * 0.5, cpy = cy + (midY - cy) * 0.5;
      var path = document.createElementNS(SVG_NS, "path");
      var d = "M" + p1.x + "," + p1.y + " Q" + cpx + "," + cpy + " " + p2.x + "," + p2.y;
      path.setAttribute("d", d);
      path.setAttribute("class", "edge");
      // Stroke width: 0.5 to 4, scaled by count/maxCount
      var w = 0.5 + (e.count / maxCount) * 3.5;
      path.setAttribute("stroke-width", w.toFixed(1));
      path.setAttribute("aria-label", e.from + " assisted " + e.to + " " + e.count + " times");
      svg.appendChild(path);
    });

    // Draw nodes
    nodes.forEach(function (n) {
      var pos = nodePos[n];
      var g = document.createElementNS(SVG_NS, "g");
      g.setAttribute("role", "listitem");
      g.setAttribute("aria-label", n + " (" + countAssists(n, edges) + " assists)");

      var circle = document.createElementNS(SVG_NS, "circle");
      circle.setAttribute("cx", pos.x);
      circle.setAttribute("cy", pos.y);
      circle.setAttribute("r", 14);
      circle.setAttribute("class", "node-circle");
      g.appendChild(circle);

      var label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", pos.x);
      label.setAttribute("y", pos.y + 22);
      label.setAttribute("class", "node-label");
      label.textContent = n;
      g.appendChild(label);

      svg.appendChild(g);
    });

    container.innerHTML = "";
    container.appendChild(svg);

    // Legend
    var legend = document.createElement("div");
    legend.className = "legend";
    legend.setAttribute("role", "note");
    legend.innerHTML = '<span class="legend-line" style="height:1px"></span><span>1 assist</span>' +
      '<span class="legend-line" style="height:4px;margin-left:8px"></span><span>' + maxCount + ' assists (max)</span>';
    container.appendChild(legend);
  }

  function countAssists(node, edges) {
    var c = 0;
    edges.forEach(function (e) { if (e.from === node || e.to === node) c += e.count; });
    return c;
  }

  function init() {
    var mount = document.getElementById("assistGraphMount");
    if (!mount) {
      // Auto-mount: find or create the panel in cockpit
      var cockpit = document.querySelector("[data-panel=cockpit]");
      if (!cockpit) return;
      mount = document.createElement("div");
      mount.id = "assistGraphMount";
      mount.className = "ckassg";
      mount.setAttribute("role", "region");
      mount.setAttribute("aria-label", "Cross-lane assist graph");
      cockpit.appendChild(mount);
    }

    mount.appendChild(css());
    mount.innerHTML += '<div class="empty-state" role="status">Loading assist data\u2026</div>';

    fetch(API).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .catch(function () { return fetch(FALLBACK).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); })
      .then(function (data) { mount.innerHTML = ""; render(mount, data); })
      .catch(function () {
        mount.innerHTML = '<div class="empty-state" role="alert">Assist graph unavailable.</div>';
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
