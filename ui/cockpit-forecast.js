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

    // Functional capability chain + 30-day outcomes (PM view)
    const plan = data.plan || {};
    if (plan.capability_chain && plan.capability_chain.length) {
      html += '<div class="fc-pm"><div class="fc-pm-title">Capability chain - each step unblocks the next</div><ol class="fc-chain">';
      plan.capability_chain.forEach(c => {
        const cls = c.status === 'in-plan' ? 'in-plan' : (String(c.status).indexOf('projected') === 0 ? 'projected' : 'queued');
        const via = c.via ? (' - via ' + c.via + (c.eta ? ' ~' + String(c.eta).slice(5, 16) : '')) : '';
        html += '<li class="fc-chain-step fc-status--' + cls + '" title="' + (c.note || '') + '">' +
          '<span class="fc-chain-name">' + c.name + '</span>' +
          '<span class="fc-chain-status">' + c.status + via + '</span>' +
          '<span class="fc-chain-unlocks">unblocks: ' + c.unlocks + '</span></li>';
      });
      html += '</ol></div>';
    }
    if (plan.outcomes_30d && plan.outcomes_30d.length) {
      html += '<div class="fc-pm fc-outcomes"><div class="fc-pm-title">30-day business outcomes</div>';
      plan.outcomes_30d.forEach(o => {
        const gated = o.via ? (' - gated by ' + o.via) : '';
        html += '<div class="fc-outcome" title="' + (o.note || '') + '">' +
          '<span class="fc-outcome-name">' + o.name + '</span>' +
          '<span class="fc-outcome-window">' + o.window + '</span>' +
          '<span class="fc-outcome-status">' + o.status + gated + '</span></div>';
      });
      html += '</div>';
    }
        if (plan.outcomes_15d && plan.outcomes_15d.length) {
          html += '<div class="fc-pm fc-outcomes"><div class="fc-pm-title">15-day plan - detailed steps (derived from the 30-day plan)</div>';
          plan.outcomes_15d.forEach(e => {
            const parent = e.parent ? (' <span class="hint">&rarr; ' + e.parent + '</span>') : '';
            html += '<div class="fc-outcome" title="' + (e.note || '') + '">' +
              '<span class="fc-outcome-name">' + e.name + parent + '</span>' +
              '<span class="fc-outcome-window">' + e.window + '</span>' +
              '<span class="fc-outcome-status">' + e.status + '</span></div>';
            (e.steps || []).forEach(s => {
              html += '<div class="fc-outcome fc-step15"><span class="fc-outcome-window">' + s.days + '</span>' +
                '<span class="fc-outcome-status">' + s.text + '</span></div>';
            });
          });
          html += '</div>';
        }
        if (plan.outcomes_7d && plan.outcomes_7d.length) {
          html += '<div class="fc-pm fc-outcomes"><div class="fc-pm-title">7-day plan - daily detail (derived from the 15-day plan)</div>';
          plan.outcomes_7d.forEach(e => {
            const parent = e.parent ? (' <span class="hint">&rarr; ' + e.parent + '</span>') : '';
            html += '<div class="fc-outcome" title="clamped to days 0-7; finer sub-steps">' +
              '<span class="fc-outcome-name">' + e.name + parent + '</span>' +
              '<span class="fc-outcome-window">' + e.window + '</span>' +
              '<span class="fc-outcome-status">' + e.status + '</span></div>';
            (e.steps || []).forEach(s => {
              html += '<div class="fc-outcome fc-step15"><span class="fc-outcome-window">' + s.days + '</span>' +
                '<span class="fc-outcome-status">' + s.text + '</span></div>';
            });
          });
          html += '</div>';
        }
        if (plan.one_pager && plan.one_pager.pagers) {
          const op = plan.one_pager;
          html += '<div class="fc-pm fc-outcomes"><div class="fc-pm-title">Today\'s one-pager - per-agent plan (3 planners + judge, ' + (op.source || '') + ')</div>';
          html += '<div style="margin-bottom:4px">' + Object.keys(op.pagers).map(function(aid){return '<a href="/api/goals/onepager/'+encodeURIComponent(aid)+'" download class="dlchip">&#11015; one-pager-'+aid+'.md</a>';}).join('') + '</div>';
          Object.keys(op.pagers).forEach(aid => {
            (op.pagers[aid] || []).forEach(it => {
              const ref = it.ref ? (' <span class="hint">&larr; ' + it.ref + '</span>') : '';
              html += '<div class="fc-outcome" title="' + String(it.why || '').replace(/"/g, '&quot;') + '">' +
                '<span class="fc-outcome-name">' + aid + ': ' + it.item + ref + '</span>' +
                '<span class="fc-outcome-status"></span></div>';
            });
          });
          html += '</div>';
        }

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
