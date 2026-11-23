/* cockpit-decay.js — Confidence decay computation + application
   Cycle-12 Goal 6 | Designer | 2026-11-24
*/
const DecayController = (() => {
  let tickInterval = null;

  function init(root, options = {}) {
    const container = root || document;
    const rateHours = options.rateHours || parseInt(
      getComputedStyle(document.documentElement).getPropertyValue('--decay-rate-hours')
    ) || 168;

    // Apply initial decay state to all .decay-goal elements
    applyDecay(container, rateHours);

    // Periodic tick: re-evaluate every hour
    tickInterval = setInterval(() => applyDecay(container, rateHours), 3600000);
  }

  function computeStep(lastVerifiedAt, rateHours) {
    if (!lastVerifiedAt) return 0;
    const hoursSince = (Date.now() - new Date(lastVerifiedAt).getTime()) / 3600000;
    if (hoursSince < 24) return 0;        // fresh
    if (hoursSince < rateHours) return 1;  // 24h to decay window
    if (hoursSince < rateHours * 4) return 2; // 4x window
    return 3;                              // very stale
  }

  function applyDecay(container, rateHours) {
    container.querySelectorAll('.decay-goal').forEach(el => {
      const lastVerified = el.getAttribute('data-verified-at');
      const step = computeStep(lastVerified, rateHours);
      el.setAttribute('data-decay', String(step));
      // Update staleness label
      let label = el.querySelector('.decay-stale-label');
      if (!label) {
        label = document.createElement('span');
        label.className = 'decay-stale-label';
        el.appendChild(label);
      }
      if (step > 0 && lastVerified) {
        const days = Math.floor((Date.now() - new Date(lastVerified).getTime()) / 86400000);
        label.textContent = `${days}d since verify`;
      } else {
        label.textContent = '';
      }
    });
  }

  // Re-verify API: snap back to full confidence
  function reverify(goalId) {
    const el = document.querySelector(`.decay-goal[data-goal-id="${goalId}"]`);
    if (el) {
      el.setAttribute('data-decay', '0');
      el.setAttribute('data-verified-at', new Date().toISOString());
    }
  }

  function destroy() { clearInterval(tickInterval); }

  return { init, computeStep, reverify, destroy };
})();
