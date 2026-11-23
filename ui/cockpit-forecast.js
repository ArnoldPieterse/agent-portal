/* cockpit-forecast.js — Predictive Risk Surface (Forward-Looking)
   Cycle-12 Goal 4 | Designer | 2026-11-24
   Renders next10.json forecast data as horizontal timeline with confidence bands.
*/
const ForecastPanel = (() => {
  let container = null;

  function init(root) {
    container = root || document.querySelector('[data-forecast]') || document.getElementById('forecast-panel');
    if (!container) { console.warn('[ForecastPanel] no container found'); return; }
    loadAndRender();
  }

  async function loadAndRender() {
    try {
      const resp = await fetch('/api/goals/next10.json');
      const data = await resp.json();
      render(data);
    } catch (e) {
      renderEmpty();
    }
  }

  function render(data) {
    if (!data || !data.next10 || data.next10.length === 0) { renderEmpty(); return; }
    const next10 = data.next10;
    const fleet = data.fleet || { pct: 0, total: 0 };

    let html = '<div class="fc-timeline">';
    // Past calibration strip (last 5 cycles actual vs predicted)
    if (data.past && data.past.length > 0) {
      html += renderCalibration(data.past);
    }
    // Future: 1-10 cycles ahead
    next10.forEach((item, i) => {
      const band = getBand(item.p_reached || 0);
      html += `<div class="fc-point fc-band--${band}" data-cycle="${i+1}" title="${item.title || ''}">
        <span class="fc-dot"></span>
        <span class="fc-label">${Math.round((item.p_reached||0)*100)}%</span>
      </div>`;
    });
    // All-clear ETA marker
    const allClear = next10.find(item => (item.p_reached || 0) >= 0.95);
    if (allClear) {
      const idx = next10.indexOf(allClear);
      html += `<div class="fc-eta" style="left: ${((idx+1)/next10.length)*100}%">
        <span class="fc-eta-marker">✓</span>
        <span class="fc-eta-label">All-clear ETA: cycle ${idx+1}</span>
      </div>`;
    }
    html += '</div>';

    // Fleet status header
    html = `<div class="fc-header">
      <span class="fc-fleet-pct">${fleet.pct || 0}/${fleet.total || 0} goals</span>
      <span class="fc-throughput">${data.throughput ? data.throughput + '/cycle' : ''}</span>
    </div>` + html;

    container.innerHTML = html;
  }

  function renderCalibration(past) {
    let strip = '<div class="fc-calibration">';
    past.slice(-5).forEach((p, i) => {
      const match = (p.actual >= p.predicted) ? 'match' : 'miss';
      strip += `<span class="fc-cal-dot fc-cal--${match}" title="Cycle ${i+1}: predicted ${Math.round(p.predicted*100)}%, actual ${Math.round(p.actual*100)}%"></span>`;
    });
    strip += '</div>';
    return strip;
  }

  function getBand(p) {
    if (p >= 0.7) return 'high';
    if (p >= 0.4) return 'med';
    return 'low';
  }

  function renderEmpty() {
    container.innerHTML = '<div class="fc-empty">Insufficient data for forecast</div>';
  }

  return { init, render, getBand, renderCalibration };
})();
