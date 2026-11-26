/* ui/cockpit-convergence-velocity.js  (staged assist for Designer goal #5 — Pixel, 2026-11-27)
 *
 * Convergence Velocity Indicator
 *   - 120x32 SVG sparkline of the last 8 cycle autonomy scores.
 *   - Directional arrow (accelerating / stable / decelerating) from the least-squares
 *     slope of that window; arrow matches the slope sign.
 *   - Self-contained IIFE, no external deps, token-only colors (no hardcoded hex),
 *     fully static => reduced-motion safe by construction.
 *
 * LANDING (White seat only — do NOT apply from a sandbox seat): copy this file to
 *   ui/cockpit-convergence-velocity.js and advance the pin (memory_mirror.py PIN_FILES).
 * The module injects its own scoped <style> and reads #ckconvVelocity, so the only
 * markup needed is:  <div id="ckconvVelocity"></div> inside the convergence section,
 * plus  <script src="ui/cockpit-convergence-velocity.js" defer></script>.
 * Data source: /api/convergence -> score_history (array of {score, mode?, cycle?}).
 */
(function () {
  "use strict";
  var API = "/api/convergence";
  var MOUNT = "ckconvVelocity";
  var W = 120, H = 32, PAD = 3;   // sparkline canvas + inner padding
  var N = 8;                      // last N cycles (<=8)
  var SLOPE_BAND = 1.5;           // |slope| <= band => "stable" (score pts / cycle)

  function el(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>\"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // least-squares slope of vals over index 0..n-1 => score points per cycle.
  function slope(vals) {
    var n = vals.length, sx = 0, sy = 0, sxy = 0, sxx = 0;
    for (var i = 0; i < n; i++) { sx += i; sy += vals[i]; sxy += i * vals[i]; sxx += i * i; }
    var den = n * sxx - sx * sx;
    return den === 0 ? 0 : (n * sxy - sx * sy) / den;
  }

  function classify(s) {
    if (s > SLOPE_BAND) return { key: "accelerating", glyph: "\u2191", label: "accelerating" };
    if (s < -SLOPE_BAND) return { key: "decelerating", glyph: "\u2193", label: "decelerating" };
    return { key: "stable", glyph: "\u2192", label: "stable" };
  }

  function emptyState(word) {
    var host = el(MOUNT);
    if (!host) return;
    host.innerHTML = '<span class="ckconv-vel-empty" role="img" aria-label="Convergence velocity: ' +
      esc(word) + '">\u2014</span>';
  }

  function render(data) {
    var host = el(MOUNT);
    if (!host) return;
    var hist = (data && data.score_history) || [];
    hist = hist.filter(function (p) { return p && p.score != null && isFinite(p.score); });
    if (hist.length < 2) { emptyState("insufficient history"); return; }

    var win = hist.slice(-N);
    var vals = win.map(function (p) { return p.score; });
    var mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals);
    var span = (mx - mn) || 1;
    var iw = W - PAD * 2, ih = H - PAD * 2;
    function X(i) { return win.length === 1 ? PAD + iw / 2 : (PAD + (i / (win.length - 1)) * iw); }
    function Y(v) { return PAD + ih - ((v - mn) / span) * ih; }

    var line = vals.map(function (v, i) { return X(i).toFixed(1) + "," + Y(v).toFixed(1); }).join(" ");
    var area = "M" + X(0).toFixed(1) + "," + (H - PAD) + " L" +
      vals.map(function (v, i) { return X(i).toFixed(1) + "," + Y(v).toFixed(1); }).join(" L") +
      " L" + X(vals.length - 1).toFixed(1) + "," + (H - PAD) + " Z";

    var s = slope(vals), c = classify(s);
    var first = Math.round(vals[0]), last = Math.round(vals[vals.length - 1]);
    var aria = "Convergence velocity: " + c.label + ", score " + (s >= 0 ? "rose" : "fell") +
      " from " + first + " to " + last + " over the last " + win.length + " cycles.";

    host.innerHTML =
      '<span class="ckconv-vel" role="img" aria-label="' + esc(aria) + '">' +
        '<svg viewBox="0 0 ' + W + " " + H + '" width="' + W + '" height="' + H + '" ' +
          'preserveAspectRatio="none" aria-hidden="true" focusable="false">' +
          '<title>Convergence velocity: ' + esc(c.label) + ' (' + first + "\u2192" + last + ")</title>" +
          '<path class="ckconv-vel-area" d="' + area + '" fill="var(--acc)" fill-opacity="0.12"></path>' +
          '<polyline class="ckconv-vel-line" points="' + line + '" fill="none" stroke="var(--acc)" ' +
            'stroke-width="1.5" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"></polyline>' +
          '<circle cx="' + X(vals.length - 1).toFixed(1) + '" cy="' + Y(last).toFixed(1) + '" r="2" fill="var(--acc)"></circle>' +
        '</svg>' +
        '<span class="ckconv-vel-arrow ckconv-vel-' + c.key + '" aria-hidden="true">' + c.glyph + "</span>" +
        '<span class="ckconv-vel-word">' + esc(c.label) + "</span>" +
      "</span>";
  }

  // Scoped, token-only CSS (no hardcoded hex); idempotent so re-injection is a no-op.
  function injectCSS() {
    if (document.getElementById("ckconvVelCss")) return;
    var css = [
      "#ckconvVelocity{display:inline-flex;align-items:center;gap:6px;font-size:12px;line-height:1;color:var(--text)}",
      ".ckconv-vel{display:inline-flex;align-items:center;gap:5px}",
      ".ckconv-vel svg{display:block}",
      ".ckconv-vel-arrow{font-size:13px;line-height:1}",
      ".ckconv-vel-accelerating{color:var(--ok)}",
      ".ckconv-vel-stable{color:var(--dim)}",
      ".ckconv-vel-decelerating{color:var(--err)}",
      ".ckconv-vel-word{font-size:11px;color:var(--text);opacity:.85}",
      ".ckconv-vel-empty{color:var(--dim);font-size:12px}"
    ].join("\n");
    var st = document.createElement("style");
    st.id = "ckconvVelCss";
    st.textContent = css;
    (document.head || document.documentElement).appendChild(st);
  }

  function refresh() {
    if (!el(MOUNT)) return;
    fetch(API, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(render)
      .catch(function () { emptyState("unavailable"); });
  }

  function init() {
    injectCSS();
    refresh();
    setInterval(refresh, 60000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
