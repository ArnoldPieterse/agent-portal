/* ui/fleet_health_gauge.js  (staged assist for Designer goal #3 — Pixel, 2026-11-27)
 *
 * Fleet Health Composite Gauge
 *   - A single 0-100 number blending four autonomy-convergence components:
 *       completion rate, intervention pressure, cycle-duration stability, OOM recovery.
 *   - Documented fixed weights that sum to exactly 1; when a component source is
 *     unavailable its weight is renormalized over the available set (a down-source
 *     never silently drags the score), and the full-data path uses weights as-is.
 *   - Polls /api/health as the liveness HEARTBEAT (per AC "updates on /api/health poll");
 *     each clean heartbeat re-gathers components from their sources and re-renders.
 *   - Tooltip shows the per-component breakdown (value x weight = contribution).
 *   - Self-contained IIFE, no external deps, token-only colors (no hardcoded hex),
 *     ring is static under prefers-reduced-motion => reduced-motion safe by construction.
 *
 * LANDING (White seat only — do NOT apply from a sandbox seat): copy this file to
 *   ui/fleet_health_gauge.js and advance the pin (memory_mirror.py PIN_FILES).
 * The module injects its own scoped <style> and reads #fleetHealthGauge, so the only
 * markup needed is:  <div id="fleetHealthGauge"></div> in the fleet panel,
 * plus  <script src="ui/fleet_health_gauge.js" defer></script>.
 *
 * DATA CONTRACT (grounded in agent_portal.py, 2026-11-27):
 *   /api/health -> {ok, service, uptime_s}                       (heartbeat only)
 *   /api/goals  -> {fleet_pct, fleet_done, fleet_total, agents[]} (completion rate)
 *   /api/convergence -> {score_history:[{score,...}]}             (intervention pressure proxy)
 *   intervention / duration-stability / oom-recovery are best-effort: each falls back to a
 *     documented neutral 50 when its source is absent, and the composite renormalizes.
 */
(function () {
  "use strict";

  /* ---- Documented formula (weights sum to exactly 1) ------------------------- */
  var WEIGHTS = {
    completion:   0.35,
    intervention: 0.25,
    duration:     0.20,
    oom:          0.20
  };
  var NEUTRAL = 50;      // value assigned to a component whose source is unavailable
  var HEARTBEAT_MS = 30000;

  /* Pure, dependency-free math — exported for unit testing (window.FleetHealthGauge). */

  // clamp any number into [lo, hi]
  function clamp(v, lo, hi) { v = +v; if (!isFinite(v)) return lo; return Math.max(lo, Math.min(hi, v)); }

  /* Each normalizer maps a raw signal to a 0-100 health value (higher = healthier).
   * Returns null when the signal is absent so the caller can apply NEUTRAL + renormalize. */
  function normCompletion(fleetPct) {
    if (fleetPct == null || !isFinite(+fleetPct)) return null;
    return clamp(fleetPct, 0, 100);
  }
  // intervention pressure: recent score drops erode autonomy. ~5 pts/cycle of drop => full penalty.
  function normIntervention(scoreHistory) {
    if (!Array.isArray(scoreHistory) || scoreHistory.length < 2) return null;
    var vals = scoreHistory.map(function (p) { return p && isFinite(+p.score) ? +p.score : null; })
                           .filter(function (v) { return v != null; });
    if (vals.length < 2) return null;
    var drops = 0;
    for (var i = 1; i < vals.length; i++) { if (vals[i - 1] > vals[i]) drops += (vals[i - 1] - vals[i]); }
    var pressure = clamp(drops, 0, 100);          // total eroded points, capped
    return clamp(100 - pressure, 0, 100);
  }
  // duration stability: lower coefficient-of-variation of cycle durations => higher.
  function normDuration(durations) {
    if (!Array.isArray(durations)) return null;
    var xs = durations.map(Number).filter(function (v) { return isFinite(v) && v > 0; });
    if (xs.length < 2) return null;
    var mean = xs.reduce(function (a, b) { return a + b; }, 0) / xs.length;
    if (mean <= 0) return null;
    var varr = xs.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / xs.length;
    var cv = Math.sqrt(varr) / mean;              // coefficient of variation
    return clamp(100 - cv * 100, 0, 100);
  }
  // oom recovery: recovered/total; no recent OOMs => healthy (100).
  function normOom(total, recovered) {
    var t = +total, r = +recovered;
    if (!isFinite(t)) return null;
    if (t <= 0) return 100;                        // nothing to recover from
    r = isFinite(r) ? r : 0;
    return clamp(100 * (r / t), 0, 100);
  }

  /* Composite: weighted blend over AVAILABLE components only (renormalized).
   * Returns {value:0-100 float, breakdown:[{key,label,value,weight,contribution,available}], available:n} */
  function composite(raw) {
    raw = raw || {};
    var parts = [
      { key: "completion",   label: "Completion rate",     value: normCompletion(raw.fleetPct),        w: WEIGHTS.completion },
      { key: "intervention", label: "Intervention pressure", value: normIntervention(raw.scoreHistory),  w: WEIGHTS.intervention },
      { key: "duration",     label: "Duration stability",    value: normDuration(raw.durations),         w: WEIGHTS.duration },
      { key: "oom",          label: "OOM recovery",          value: normOom(raw.oomTotal, raw.oomRecovered), w: WEIGHTS.oom }
    ];
    var num = 0, den = 0, breakdown = [];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i], avail = p.value != null;
      var effValue = avail ? p.value : NEUTRAL;
      // renormalize over the full documented weight set so a missing source neither
      // vanishes nor drags: it contributes its neutral value at full documented weight.
      num += p.w * effValue; den += p.w;
      breakdown.push({
        key: p.key, label: p.label, available: avail,
        value: avail ? Math.round(p.value) : null, baseline: avail ? null : NEUTRAL,
        weight: p.w, contribution: +(p.w * effValue).toFixed(2)
      });
    }
    var value = den > 0 ? clamp(num / den, 0, 100) : NEUTRAL;
    return { value: value, breakdown: breakdown, available: parts.filter(function (p) { return p.value != null; }).length };
  }

  function toneOf(v) { if (v >= 80) return "ok"; if (v >= 50) return "warn"; return "err"; }
  function toneVar(t) { return t === "ok" ? "var(--ok)" : t === "warn" ? "var(--warn)" : "var(--err)"; }

  /* ---- Render ---------------------------------------------------------------- */
  var MOUNT = "fleetHealthGauge";
  function el(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>\"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function emptyState(word) {
    var host = el(MOUNT); if (!host) return;
    host.innerHTML = '<span class="fhg-empty" role="img" aria-label="Fleet health: ' + esc(word) + '">\u2014</span>';
  }

  function render(result) {
    var host = el(MOUNT); if (!host) return;
    var v = Math.round(result.value), tone = toneOf(v);
    // SVG ring: r=30, circumference ~188.5; fill fraction = value/100.
    var R = 30, CIRC = 2 * Math.PI * R;
    var off = CIRC * (1 - clamp(result.value, 0, 100) / 100);

    // accessible breakdown text (always in DOM for screen readers)
    var bits = result.breakdown.map(function (b) {
      var valTxt = b.available ? b.value : "n/a";
      return b.label + ": " + valTxt + (b.available ? " (w " + b.weight + ", contrib " + b.contribution + ")" : " (baseline " + b.baseline + ")");
    });
    var aria = "Fleet health composite " + v + " out of 100, " + tone + ". Breakdown: " + bits.join("; ") + ".";

    var rows = result.breakdown.map(function (b) {
      var dot = b.available ? toneVar(toneOf(b.value)) : "var(--dim)";
      var valTxt = b.available ? b.value : "\u2014";
      return '<li class="fhg-row"><span class="fhg-dot" style="background:' + dot + '"></span>' +
             '<span class="fhg-k">' + esc(b.label) + '</span>' +
             '<span class="fhg-v">' + valTxt + '</span>' +
             '<span class="fhg-c">+' + b.contribution.toFixed(1) + '</span></li>';
    }).join("");

    host.innerHTML =
      '<div class="fhg" role="img" tabindex="0" aria-label="' + esc(aria) + '" aria-describedby="fhgDesc">' +
        '<svg viewBox="0 0 76 76" width="76" height="76" aria-hidden="true" focusable="false">' +
          '<circle class="fhg-track" cx="38" cy="38" r="' + R + '" fill="none" stroke="var(--line)" stroke-width="6"></circle>' +
          '<circle class="fhg-arc fhg-' + tone + '" cx="38" cy="38" r="' + R + '" fill="none" ' +
            'stroke="' + toneVar(tone) + '" stroke-width="6" stroke-linecap="round" ' +
            'stroke-dasharray="' + CIRC.toFixed(2) + '" stroke-dashoffset="' + off.toFixed(2) + '" ' +
            'transform="rotate(-90 38 38)"></circle>' +
          '<text class="fhg-num" x="38" y="38" text-anchor="middle" dominant-baseline="central" fill="' + toneVar(tone) + '">' + v + '</text>' +
        '</svg>' +
        '<span class="fhg-word fhg-' + tone + '">' + tone + '</span>' +
      '</div>' +
      '<ul id="fhgDesc" class="fhg-desc" aria-label="Fleet health component breakdown">' + rows + '</ul>';
  }

  /* Scoped, token-only CSS (no hardcoded hex); idempotent so re-injection is a no-op. */
  function injectCSS() {
    if (document.getElementById("fhgCss")) return;
    var css = [
      "#fleetHealthGauge{display:inline-flex;flex-direction:column;align-items:center;gap:6px}",
      ".fhg{position:relative;display:inline-flex;align-items:center;justify-content:center;border-radius:var(--br-lg);cursor:default;outline:none}",
      ".fhg:focus-visible{box-shadow:0 0 0 2px var(--focus)}",
      ".fhg-num{font-size:22px;font-weight:700}",
      ".fhg-word{font-size:11px;color:var(--dim);letter-spacing:.04em}",
      ".fhg-desc{list-style:none;margin:0;padding:0;display:none;min-width:172px;background:var(--panel2);border:1px solid var(--line);border-radius:var(--br-md);padding:8px 10px;font-size:11px}",
      ".fhg:hover .fhg-desc,.fhg:focus-within .fhg-desc{display:block;position:absolute;top:calc(100% + 4px);left:50%;transform:translateX(-50%);z-index:5}",
      ".fhg-row{display:flex;align-items:center;gap:6px;line-height:1.5;color:var(--text)}",
      ".fhg-dot{width:8px;height:8px;border-radius:50%;flex:0 0 auto}",
      ".fhg-k{color:var(--dim)} .fhg-v{margin-left:auto;font-variant-numeric:tabular-nums}",
      ".fhg-c{color:var(--faint);font-variant-numeric:tabular-nums;min-width:34px;text-align:right}",
      ".fhg-empty{color:var(--dim);font-size:12px}",
      /* reduced motion: kill the arc transition (the static value is already correct) */
      "@media (prefers-reduced-motion: no-preference){ .fhg-arc{transition:stroke-dashoffset .4s ease} }"
    ].join("\n");
    var st = document.createElement("style");
    st.id = "fhgCss";
    st.textContent = css;
    (document.head || document.documentElement).appendChild(st);
  }

  /* ---- Data gathering (best-effort, grounded sources + neutral fallbacks) ---- */
  function jget(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status); return r.json();
    });
  }
  function gather() {
    // completion rate (grounded): /api/goals -> fleet_pct
    var c = jget("/api/goals").then(function (d) { return d && typeof d.fleet_pct === "number" ? d.fleet_pct : null; })
        .catch(function () { return null; });
    // intervention pressure (proxy): /api/convergence -> score_history
    var i = jget("/api/convergence").then(function (d) { return d && Array.isArray(d.score_history) ? d.score_history : null; })
        .catch(function () { return null; });
    // duration stability + oom recovery: best-effort from /api/goals/history (may be absent).
    var h = jget("/api/goals/history").then(function (d) {
      if (!d || !Array.isArray(d)) return { durations: null, oomTotal: null, oomRecovered: null };
      var durs = d.map(function (x) { return x && (x.duration_s != null ? x.duration_s : x.minutes); }).filter(function (v) { return isFinite(+v); });
      var ooms = d.filter(function (x) { return x && x.oom; });
      var rec = ooms.filter(function (x) { return x.recovered; });
      return { durations: durs.length ? durs : null, oomTotal: ooms.length || null, oomRecovered: ooms.length ? rec.length : null };
    }).catch(function () { return { durations: null, oomTotal: null, oomRecovered: null }; });

    return Promise.all([c, i, h]).then(function (parts) {
      return composite({ fleetPct: parts[0], scoreHistory: parts[1], durations: parts[2].durations,
                         oomTotal: parts[2].oomTotal, oomRecovered: parts[2].oomRecovered });
    });
  }

  /* Heartbeat per AC: /api/health is the poll trigger; a clean beat re-gathers + re-renders. */
  function tick() {
    jget("/api/health")
      .then(function (hb) { if (!hb || hb.ok === false) throw new Error("heartbeat not ok"); return gather(); })
      .then(render)
      .catch(function () { emptyState("unavailable"); });
  }

  function init() {
    injectCSS();
    if (!el(MOUNT)) return;
    tick();
    setInterval(tick, HEARTBEAT_MS);
  }

  // export pure math for unit testing (no DOM needed)
  window.FleetHealthGauge = { WEIGHTS: WEIGHTS, composite: composite, normCompletion: normCompletion,
    normIntervention: normIntervention, normDuration: normDuration, normOom: normOom, clamp: clamp };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
