/* cockpit-density.js — DensityController: auto-trigger + scroll preservation
   Cycle-12 Goal 1 | Designer | 2026-11-24
   Usage: include after cockpit-density.css; call DensityController.init() on DOM ready.
*/
const DensityController = (() => {
  let container = null;
  let currentMode = 'calm';
  let scrollMap = new Map();
  let debounceTimer = null;

  function init(root) {
    container = root || document.querySelector('.ckp') || document.querySelector('[data-ckp]');
    if (!container) { console.warn('[DensityController] no .ckp container found'); return; }
    container.classList.add('ckp--calm');
    currentMode = 'calm';

    // MutationObserver: watch data-health on all panels for auto-trigger
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type !== 'attributes' || m.attributeName !== 'data-health') continue;
        const val = m.target.getAttribute('data-health');
        if (val === 'critical' || val === 'degrading') {
          setMode('incident');
          return; // stop watching once incident mode is active
        }
      }
    });

    container.querySelectorAll('.ckp__panel, .panel--health, .panel--agents').forEach(el => {
      observer.observe(el, { attributes: true, attributeFilter: ['data-health'] });
    });
  }

  function setMode(mode) {
    if (!container || mode === currentMode) return;
    const prevMode = currentMode;
    currentMode = mode;

    // Snapshot scroll positions before transition
    snapshotScroll();

    container.classList.remove(`ckp--${prevMode}`);
    container.classList.add(`ckp--${mode}`);

    // Restore scroll after transition completes
    const dur = parseInt(getComputedStyle(document.documentElement)
      .getPropertyValue('--density-transition')) || 0;
    setTimeout(() => restoreScroll(), dur + 20);
  }

  function snapshotScroll() {
    if (!container) return;
    container.querySelectorAll('.ckp__panel, [class*="panel"]').forEach(el => {
      scrollMap.set(el, { top: el.scrollTop, left: el.scrollLeft });
    });
  }

  function restoreScroll() {
    scrollMap.forEach((pos, el) => {
      if (el.isConnected) { el.scrollTop = pos.top; el.scrollLeft = pos.left; }
    });
    scrollMap.clear();
  }

  // Debounced all-clear: when no panels are critical/degrading for 2s, revert to calm
  function scheduleAllClear() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (!container) return;
      const anyCritical = container.querySelector(
        '[data-health="critical"], [data-health="degrading"]'
      );
      if (!anyCritical && currentMode === 'incident') setMode('calm');
    }, 2000);
  }

  return { init, setMode, getMode: () => currentMode, scheduleAllClear };
})();
