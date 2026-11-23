/* Fleet Topology Visualizer (Builder cycle-14 goal 6): SVG 4-host map.
   Nodes = hosts, edges = model/agent bindings; color by load; tooltip VRAM/CPU. */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  /* Fixed layout: 4 hosts in a diamond, agents orbiting their host */
  var HOST_POS = {
    White: { x: 175, y: 60 },
    Black: { x: 375, y: 60 },
    Red:   { x: 175, y: 240 },
    Blue:  { x: 375, y: 240 }
  };

  /* Agent→host bindings (derived from agents.json studio IPs) */
  var AGENT_HOST_MAP = {
    orchestrator: "White",
    researcher:   "White",
    builder:      "Black",
    verifier:     "Black",
    designer:     "Red",
    archivist:    "Red",
    scribe:       "Blue",
    mechanic:     "Blue"
  };

  function vramColor(pct) {
    if (pct == null) return "#5a6070";
    if (pct > 90) return "#e5534b";
    if (pct > 70) return "#d4a017";
    return "#2ea36b";
  }

  function buildSvg(hosts, agents) {
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 550 340");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "auto");
    svg.style.maxWidth = "550px";
    svg.style.display = "block";
    svg.style.margin = "0 auto";

    /* Background */
    var bg = document.createElementNS(NS, "rect");
    bg.setAttribute("width", "550"); bg.setAttribute("height", "340");
    bg.setAttribute("fill", "#0d1117"); bg.setAttribute("rx", "8");
    svg.appendChild(bg);

    /* Build host lookup */
    var hMap = {};
    (hosts || []).forEach(function (h) { hMap[h.name] = h; });

    /* Draw edges first (behind nodes) */
    var edgeGroup = document.createElementNS(NS, "g");
    edgeGroup.setAttribute("class", "topo-edges");
    svg.appendChild(edgeGroup);

    var edgeCount = 0;
    Object.keys(AGENT_HOST_MAP).forEach(function (agentId) {
      var hostName = AGENT_HOST_MAP[agentId];
      var hp = HOST_POS[hostName];
      if (!hp) return;
      /* Position agent as small circle offset from host center */
      var agentsOnHost = Object.keys(AGENT_HOST_MAP).filter(function (a) { return AGENT_HOST_MAP[a] === hostName; });
      var idx = agentsOnHost.indexOf(agentId);
      var angle = (idx * Math.PI * 2 / agentsOnHost.length) - Math.PI / 2;
      var r = 50;
      var ax = hp.x + r * Math.cos(angle);
      var ay = hp.y + r * Math.sin(angle);

      /* Edge line */
      var line = document.createElementNS(NS, "line");
      line.setAttribute("x1", hp.x); line.setAttribute("y1", hp.y);
      line.setAttribute("x2", ax);   line.setAttribute("y2", ay);
      line.setAttribute("stroke", "#3a4050"); line.setAttribute("stroke-width", "1.5");
      line.setAttribute("stroke-dasharray", "4,3");
      edgeGroup.appendChild(line);

      /* Agent node (small circle) */
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", ax); c.setAttribute("cy", ay);
      c.setAttribute("r", "10");
      c.setAttribute("fill", "#232833");
      c.setAttribute("stroke", "#4a7ddb");
      c.setAttribute("stroke-width", "1.5");

      /* Agent label */
      var txt = document.createElementNS(NS, "text");
      txt.setAttribute("x", ax); txt.setAttribute("y", ay + 22);
      txt.setAttribute("text-anchor", "middle");
      txt.setAttribute("fill", "#8a8f98");
      txt.setAttribute("font-size", "9");
      txt.textContent = agentId;

      edgeGroup.appendChild(c);
      edgeGroup.appendChild(txt);
      edgeCount++;
    });

    /* Draw host nodes on top */
    var nodeGroup = document.createElementNS(NS, "g");
    nodeGroup.setAttribute("class", "topo-nodes");
    svg.appendChild(nodeGroup);

    Object.keys(HOST_POS).forEach(function (hostName) {
      var pos = HOST_POS[hostName];
      var h = hMap[hostName] || {};
      var color = vramColor(h.vram_pct);

      /* Outer ring */
      var ring = document.createElementNS(NS, "circle");
      ring.setAttribute("cx", pos.x); ring.setAttribute("cy", pos.y);
      ring.setAttribute("r", "28");
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", color);
      ring.setAttribute("stroke-width", "3");
      ring.setAttribute("opacity", "0.6");

      /* Inner circle */
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", pos.x); c.setAttribute("cy", pos.y);
      c.setAttribute("r", "22");
      c.setAttribute("fill", color);
      c.setAttribute("opacity", "0.85");

      /* Host label */
      var txt = document.createElementNS(NS, "text");
      txt.setAttribute("x", pos.x); txt.setAttribute("y", pos.y + 4);
      txt.setAttribute("text-anchor", "middle");
      txt.setAttribute("fill", "#e8eaed");
      txt.setAttribute("font-size", "11");
      txt.setAttribute("font-weight", "700");
      txt.textContent = hostName;

      /* Tooltip */
      var title = document.createElementNS(NS, "title");
      var vram = h.vram_pct != null ? h.vram_pct + "%" : "N/A";
      var cpu  = h.cpu_pct  != null ? h.cpu_pct  + "%" : "N/A";
      var temp = h.temp_c   != null ? h.temp_c   + "\u00B0C" : "N/A";
      title.textContent = hostName + ": VRAM " + vram + ", CPU " + cpu + ", Temp " + temp;

      nodeGroup.appendChild(ring);
      nodeGroup.appendChild(c);
      nodeGroup.appendChild(txt);
      c.appendChild(title);
    });

    return { svg: svg, edgeCount: edgeCount };
  }

  function render(container, hosts, agents) {
    if (!container) return;
    container.innerHTML = "";
    var result = buildSvg(hosts, agents);
    container.appendChild(result.svg);
  }

  window.CockpitTopology = {
    render: render,
    buildSvg: buildSvg,
    HOST_POS: HOST_POS,
    AGENT_HOST_MAP: AGENT_HOST_MAP
  };
})();
