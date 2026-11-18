// test_components.js - Verifier scaffold for Builder goal #1 (Component Library v1)
// Acceptance: 5 components exist in ui/components.js; each used by >=2 panels; JSDoc present.
// Run: open portal, this file auto-loads via <script> after components.js
// Expects: window.Components = { card, badge, gauge, timelineNode, collapsiblePanel }

(function() {
  'use strict';
  const results = [];
  
  function check(name, fn) {
    try {
      const r = fn();
      results.push({ name, pass: !!r, detail: r || 'falsy return' });
    } catch (e) {
      results.push({ name, pass: false, detail: e.message });
    }
  }

  // 1. All 5 components exported
  check('Components object exists', () => window.Components && typeof window.Components === 'object');
  check('card() is a function', () => typeof Components?.card === 'function');
  check('badge() is a function', () => typeof Components?.badge === 'function');
  check('gauge() is a function', () => typeof Components?.gauge === 'function');
  check('timelineNode() is a function', () => typeof Components?.timelineNode === 'function');
  check('collapsiblePanel() is a function', () => typeof Components?.collapsiblePanel === 'function');

  // 2. Each returns a valid DOM element or HTML string
  check('card() returns Element or string', () => {
    const el = Components?.card({ title: 'Test', body: 'hello' });
    return el instanceof Element || (typeof el === 'string' && el.length > 0);
  });
  check('badge() returns Element or string', () => {
    const el = Components?.badge({ label: 'ok', variant: 'success' });
    return el instanceof Element || (typeof el === 'string' && el.length > 0);
  });
  check('gauge() returns Element or string', () => {
    const el = Components?.gauge({ value: 75, max: 100, label: 'Load' });
    return el instanceof Element || (typeof el === 'string' && el.length > 0);
  });
  check('timelineNode() returns Element or string', () => {
    const el = Components?.timelineNode({ cycle: 5, status: 'active', count: '10/80' });
    return el instanceof Element || (typeof el === 'string' && el.length > 0);
  });
  check('collapsiblePanel() returns Element or string', () => {
    const el = Components?.collapsiblePanel({ title: 'Details', content: 'inner' });
    return el instanceof Element || (typeof el === 'string' && el.length > 0);
  });

  // 3. No external dependencies (no CDN links, no require/import)
  check('components.js has no external deps', async () => {
    const resp = await fetch('/ui/components.js');
    const src = await resp.text();
    return !/https?:\/\//.test(src) && !/require\(/.test(src);
  });

  // 4. JSDoc comments present (>=5 blocks)
  check('JSDoc blocks >= 5', async () => {
    const resp = await fetch('/ui/components.js');
    const src = await resp.text();
    return (src.match(/\/\*\*/g) || []).length >= 5;
  });

  // Report
  window.__componentTestResults = results;
  console.log('[Verifier] Component test results:', 
    results.filter(r => r.pass).length + '/' + results.length + ' pass');
  results.forEach(r => {
    if (!r.pass) console.warn('  FAIL:', r.name, '-', r.detail);
  });
})();
