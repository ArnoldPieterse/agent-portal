/* ui/components.js — Reusable UI component library v1 (Builder goal #1, cycle-5).
   parent: index.html | siblings: ui/core.js, ui/uploads.js, ui/fleet_topology.js
   rule: memory/portal/file-modularity.md | served by GET /ui/components.js

   Each component is a single factory function returning a DOM element.
   No external dependencies. All styling uses CSS custom properties (var(--...))
   from ui/app.css so both themes are supported automatically.

   Usage:
     // After all other scripts load, components are available as window.UI.*
     const el = UI.card({ title: "Fleet", badge: { label: "3", tone: "ok" } });
     container.appendChild(el);
*/
(function (root) {
  "use strict";

  /* Helpers */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  /* ------------------------------------------------------------------ */
  /* 1. CARD                                                             */
  /* ------------------------------------------------------------------ */

  /**
   * Creates a card container element.
   * Used by: agent list (core.js .acard), fleet detail panel (fleet_topology.js), goals panel.
   *
   * @param {object} opts
   * @param {string} [opts.title]     - Bold title text at top of card.
   * @param {string} [opts.subtitle]  - Dimmed subtitle under title.
   * @param {{label:string, tone?:string}} [opts.badge] - Inline badge in header (tone: "ok"|"warn"|"err"|"info").
   * @param {string} [opts.bodyHtml]  - Inner HTML for the body area.
   * @param {Function} [opts.onClick] - Click handler; sets cursor:pointer and aria role.
   * @param {boolean} [opts.selected] - Highlights border (accent color).
   * @returns {HTMLElement} A <div class="ui-card"> element.
   */
  function card(opts) {
    opts = opts || {};
    const c = el("div", "ui-card" + (opts.selected ? " ui-card--sel" : ""));
    if (opts.onClick) { c.setAttribute("role", "button"); c.setAttribute("tabindex", "0"); c.addEventListener("click", opts.onClick); }

    // Header row
    const head = el("div", "ui-card__head");
    const titleWrap = el("div", "ui-card__titles");
    if (opts.title) titleWrap.appendChild(el("b", "ui-card__title", esc(opts.title)));
    if (opts.subtitle) titleWrap.appendChild(el("span", "ui-card__sub", esc(opts.subtitle)));
    head.appendChild(titleWrap);
    if (opts.badge) head.appendChild(badge(opts.badge));
    c.appendChild(head);

    // Body
    const body = el("div", "ui-card__body");
    if (opts.bodyHtml) body.innerHTML = opts.bodyHtml;
    c.appendChild(body);
    return c;
  }

  /* ------------------------------------------------------------------ */
  /* 2. BADGE                                                            */
  /* ------------------------------------------------------------------ */

  /**
   * Creates an inline status badge (dot + label or pill).
   * Used by: agent model status dots (core.js), fleet host state (fleet_topology.js), goal cycle chips.
   *
   * @param {object} opts
   * @param {string} opts.label  - Text next to the dot (e.g. "idle", "3 open").
   * @param {string} [opts.tone] - Color tone: "ok" | "warn" | "err" | "info" | "dim". Default "dim".
   * @returns {HTMLElement} A <span class="ui-badge ui-badge--{tone}"> element.
   */
  function badge(opts) {
    opts = opts || {};
    const tone = opts.tone || "dim";
    const b = el("span", "ui-badge ui-badge--" + esc(tone));
    b.appendChild(el("span", "ui-badge__dot"));
    if (opts.label) b.appendChild(document.createTextNode(opts.label));
    return b;
  }

  /* ------------------------------------------------------------------ */
  /* 3. GAUGE                                                            */
  /* ------------------------------------------------------------------ */

  /**
   * Creates a compact circular gauge showing a score or metric.
   * Used by: fleet health dashboard (goal #3), agent card score badge, performance budget display.
   *
   * @param {object} opts
   * @param {number} opts.value    - Current value (0-100).
   * @param {number} [opts.max=100] - Maximum value for the arc.
   * @param {string} [opts.label]  - Small label under the number.
   * @param {number} [opts.size=48] - Diameter in px.
   * @returns {HTMLElement} A <div class="ui-gauge"> containing an SVG ring + center text.
   */
  function gauge(opts) {
    opts = opts || {};
    const val = Math.max(0, Math.min(opts.value || 0, opts.max || 100));
    const max = opts.max || 100;
    const size = opts.size || 48;
    const stroke = Math.max(3, size / 12);
    const r = (size - stroke) / 2;
    const circ = 2 * Math.PI * r;
    const pct = max ? val / max : 0;
    const dash = (pct * circ).toFixed(1);

    // Color by threshold: >=80 ok, >=50 warn, else err
    const tone = pct >= 0.8 ? "var(--ok,#3ddc84)" : pct >= 0.5 ? "var(--warn,#ff9f43)" : "var(--err,#e05252)";

    const g = el("div", "ui-gauge");
    g.style.cssText = "width:" + size + "px;height:" + size + "px;display:inline-flex;flex-direction:column;align-items:center;";
    g.innerHTML =
      '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + " " + size + '">' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="var(--line,#333)" stroke-width="' + stroke + '"/>' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="' + tone + '" stroke-width="' + stroke + '"' +
      ' stroke-dasharray="' + dash + " " + circ + '" stroke-linecap="round" transform="rotate(-90 ' + size / 2 + " " + size / 2 + ')"/>' +
      '<text x="' + size / 2 + '" y="' + (size / 2 + 1) + '" text-anchor="middle" dominant-baseline="middle" fill="currentColor" style="font-size:' + Math.round(size * 0.3) + 'px;font-weight:600">' + Math.round(pct * 100) + "</text>" +
      "</svg>";
    if (opts.label) {
      const lb = el("span", "ui-gauge__label");
      lb.textContent = opts.label;
      lb.style.cssText = "font-size:10px;color:var(--dim,#888);margin-top:2px;";
      g.appendChild(lb);
    }
    return g;
  }

  /* ------------------------------------------------------------------ */
  /* 4. TIMELINE NODE                                                    */
  /* ------------------------------------------------------------------ */

  /**
   * Creates a single node in a horizontal timeline strip (goal cycle nodes).
   * Used by: goal cycle timeline panel (goal #2), run history view.
   *
   * @param {object} opts
   * @param {string} opts.label    - Node label (e.g. "C3", "Cycle 4").
   * @param {number} [opts.open=0]     - Count of open items in this cycle.
   * @param {number} [opts.closed=0]   - Count of closed items.
   * @param {boolean} [opts.active=false] - Highlights as current cycle.
   * @param {Function} [opts.onClick]  - Click handler (shows popover/stats).
   * @returns {HTMLElement} A <div class="ui-tl-node"> with a circle + label.
   */
  function timelineNode(opts) {
    opts = opts || {};
    const n = el("div", "ui-tl-node" + (opts.active ? " ui-tl-node--active" : ""));
    n.setAttribute("role", "button");
    n.setAttribute("tabindex", "0");
    n.setAttribute("aria-label", opts.label + ": " + (opts.open || 0) + " open, " + (opts.closed || 0) + " closed");

    const total = (opts.open || 0) + (opts.closed || 0);
    const pct = total ? Math.round(((opts.closed || 0) / total) * 100) : 0;
    const tone = pct === 100 ? "var(--ok,#3ddc84)" : pct >= 50 ? "var(--warn,#ff9f43)" : "var(--err,#e05252)";

    n.innerHTML =
      '<div class="ui-tl-node__dot" style="background:' + tone + ';width:14px;height:14px;border-radius:50%;margin:0 auto 4px;"></div>' +
      '<span class="ui-tl-node__label">' + esc(opts.label) + "</span>" +
      '<span class="ui-tl-node__stats" style="font-size:9px;color:var(--dim,#888);">' + (opts.open || 0) + "/" + total + "</span>";

    if (opts.onClick) {
      n.addEventListener("click", opts.onClick);
      n.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); opts.onClick(e); } });
    }
    return n;
  }

  /* ------------------------------------------------------------------ */
  /* 5. COLLAPSIBLE PANEL                                                */
  /* ------------------------------------------------------------------ */

  /**
   * Creates a collapsible section with a toggle header and hidden body.
   * Used by: ops panel sections, agent detail drawer, knowledge base list.
   *
   * @param {object} opts
   * @param {string} opts.title      - Header text shown when collapsed/expanded.
   * @param {string|HTMLElement} [opts.body] - Inner HTML string or DOM element for body content.
   * @param {boolean} [opts.open=false] - Whether the panel starts expanded.
   * @param {Function} [opts.onToggle] - Callback(open: boolean) fired on expand/collapse.
   * @returns {HTMLElement} A <div class="ui-collapsible"> with aria-expanded managed automatically.
   */
  function collapsiblePanel(opts) {
    opts = opts || {};
    const p = el("div", "ui-collapsible");
    const isOpen = !!opts.open;

    const head = el("button", "ui-collapsible__head");
    head.setAttribute("aria-expanded", String(isOpen));
    head.innerHTML = '<span class="ui-collapsible__chevron" style="display:inline-block;transition:transform .2s;font-size:10px;">' + (isOpen ? "\u25bc" : "\u25b6") + '</span> ' + esc(opts.title || "Panel");

    const body = el("div", "ui-collapsible__body");
    body.style.display = isOpen ? "" : "none";
    if (typeof opts.body === "string") body.innerHTML = opts.body;
    else if (opts.body instanceof HTMLElement) body.appendChild(opts.body);

    head.addEventListener("click", () => {
      const nowOpen = head.getAttribute("aria-expanded") !== "true";
      head.setAttribute("aria-expanded", String(nowOpen));
      body.style.display = nowOpen ? "" : "none";
      head.querySelector(".ui-collapsible__chevron").textContent = nowOpen ? "\u25bc" : "\u25b6";
      if (opts.onToggle) opts.onToggle(nowOpen);
    });

    p.appendChild(head);
    p.appendChild(body);
    return p;
  }

  /* ---- Export ---- */
  root.UI = { card, badge, gauge, timelineNode, collapsiblePanel };
})(typeof window !== "undefined" ? window : this);
