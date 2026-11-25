/* Cycle Transition Animation (Designer cycle-17 goal #8)
   When cycle closes and new one begins: overlay with old→new number fade + topic scroll.
   Duration < 2s, non-blocking (pointer-events:none). Triggered by /api/fleet-mode cycle field change. */
(function () {
  "use strict";
  var API = "/api/fleet-mode";
  var DURATION = 1800; // ms total - under 2s requirement
  var prevCycle = null;
  var overlay = null;

  function css() {
    var s = document.createElement("style");
    s.textContent = [
      ".cct-overlay{position:fixed;inset:0;z-index:10000;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(12,14,18,.92);pointer-events:none;opacity:0;transition:opacity .3s ease}",
      ".cct-overlay.active{opacity:1}",
      ".cct-overlay.done{opacity:0;transition:opacity .4s ease}",
      ".cct-old,.cct-new{font-size:72px;font-weight:800;color:#e2e5ea;text-align:center;line-height:1.1}",
      ".cct-old{animation:cctFadeOut .6s ease-out forwards;opacity:1}",
      ".cct-new{animation:cctFadeIn .7s ease-in .4s both;opacity:0}",
      ".cct-topic{font-size:16px;color:#8a8f98;margin-top:12px;max-width:480px;text-align:center;overflow:hidden;white-space:nowrap;animation:cctScrollIn .5s ease-out 1.0s both}",
      "@keyframes cctFadeOut{0%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(.92)}}",
      "@keyframes cctFadeIn{0%{opacity:0;transform:scale(1.08) translateY(8px)}100%{opacity:1;transform:scale(1) translateY(0)}}",
      "@keyframes cctScrollIn{0%{clip-path:inset(0 100% 0 0);opacity:0}100%{clip-path:inset(0 0 0 0);opacity:1}}",
      "@media(prefers-reduced-motion:reduce){.cct-old,.cct-new,.cct-topic{animation:none!important;opacity:1!important;transform:none!important;clip-path:none!important}}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function show(from, to, topic) {
    if (overlay && overlay.parentNode) overlay.remove();
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return; // skip animation entirely for reduced motion users

    overlay = document.createElement("div");
    overlay.className = "cct-overlay";
    overlay.setAttribute("data-testid", "cct-overlay");
    overlay.setAttribute("aria-hidden", "true");
    overlay.innerHTML =
      '<div class="cct-old" data-testid="cct-old">' + (from || "—") + '</div>' +
      '<div class="cct-new" data-testid="cct-new">' + (to || "—") + '</div>' +
      (topic ? '<div class="cct-topic" data-testid="cct-topic">' + topic + '</div>' : '');
    document.body.appendChild(overlay);
    // Trigger reflow then activate
    void overlay.offsetWidth;
    overlay.classList.add("active");
    setTimeout(function () {
      if (overlay) { overlay.classList.add("done"); }
    }, DURATION - 400);
    setTimeout(function () {
      if (overlay && overlay.parentNode) overlay.remove();
      overlay = null;
    }, DURATION + 100);
  }

  // Public API for testing / manual trigger
  window.__cycleTransition = {
    show: show,
    prevCycle: function () { return prevCycle; },
    _detect: detect
  };

  async function poll() {
    try {
      var r = await fetch(API, { cache: "no-store" });
      if (!r.ok) return;
      var d = await r.json();
      var cur = d && d.cycle ? String(d.cycle) : null;
      if (cur !== prevCycle) {
        if (prevCycle !== null) {
          show(prevCycle, cur, d.topic || "New cycle begins");
        }
        prevCycle = cur;
      }
    } catch (e) { /* API unavailable - skip */ }
  }

  function detect() { poll(); }

  function init() {
    css();
    // Initial read to set baseline without animating
    poll();
    setInterval(poll, 10000); // check every 10s for cycle change
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
