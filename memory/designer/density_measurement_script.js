// Information Density Pass - Acceptance Test Measurement Script
// Run in DevTools Console on the portal page. Measures rendered vertical space
// per panel section and compares to baseline values.
// 
// Usage: 1) Open portal at :8099
//        2) Open DevTools (F12) -> Console
//        3) Paste and run this script
//        4) Copy output to evidence document

(function() {
  const BASELINE = {
    // Baseline values measured from pre-tokenization state (2026-11-18)
    // Format: selector -> total rendered height in px
    'fleet-panel': 412,
    'goals-panel': 385,
    'ops-panel': 298,
    'uploads-panel': 264,
    'timeline-panel': 340,
    'total-page': 1699
  };

  const results = {};
  
  function measureSection(selector) {
    const el = document.querySelector(selector);
    if (!el) return null;
    
    const rect = el.getBoundingClientRect();
    const cs = window.getComputedStyle(el);
    
    let childrenHeight = 0;
    el.querySelectorAll(':scope > *').forEach(child => {
      childrenHeight += child.getBoundingClientRect().height;
    });
    
    return {
      height: Math.round(rect.height),
      paddingTop: cs.paddingTop,
      paddingBottom: cs.paddingBottom,
      lineHeight: cs.lineHeight,
      fontSize: cs.fontSize,
      childrenCount: el.children.length,
      internalGap: Math.round(rect.height - childrenHeight)
    };
  }

  const sections = [
    { name: 'fleet-panel', sel: '.panel[data-panel="fleet"], #fleetPanel' },
    { name: 'goals-panel', sel: '.panel[data-panel="goals"], #goalsPanel' },
    { name: 'ops-panel', sel: '.panel[data-panel="ops"], #opsPanel' },
    { name: 'uploads-panel', sel: '.panel[data-panel="uploads"], #uploadsPanel' },
    { name: 'timeline-panel', sel: '.panel[data-panel="timeline"], #timelinePanel' }
  ];

  let totalHeight = 0;
  
  sections.forEach(s => {
    const data = measureSection(s.sel);
    results[s.name] = data;
    if (data) totalHeight += data.height;
    
    const baseline = BASELINE[s.name];
    if (baseline && data) {
      const change = ((data.height - baseline) / baseline * 100).toFixed(1);
      console.log("  " + s.name + ": " + data.height + "px (baseline: " + baseline + "px, change: " + change + "%)", 
        { color: parseFloat(change) < -5 ? '#3ddc84' : parseFloat(change) > 5 ? '#ff6b6b' : '#9aa7b8' });
    } else {
      console.log("  " + s.name + ": " + (data ? data.height + 'px' : 'NOT FOUND'));
    }
  });

  const pageH = document.documentElement.scrollHeight;
  results['total-page'] = { height: pageH };
  const totalChange = ((pageH - BASELINE['total-page']) / BASELINE['total-page'] * 100).toFixed(1);
  console.log("\nTOTAL PAGE: " + pageH + "px (baseline: " + BASELINE['total-page'] + "px, change: " + totalChange + "%)");

  // Check for text overlap/clipping
  console.log('\n--- CLIPPING CHECK ---');
  let clipped = 0;
  document.querySelectorAll('.panel *').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.height > 0 && el.scrollHeight > el.clientHeight + 2) {
      clipped++;
      if (clipped <= 3) console.warn("  Clipped: " + el.tagName + "." + el.className);
    }
  });
  console.log(clipped === 0 ? '  No clipping detected [OK]' : "  " + clipped + " elements with overflow");

  // Summary
  console.log('\n--- SUMMARY ---');
  const pass = parseFloat(totalChange) <= -20 && clipped === 0;
  console.log(pass ? 
    'PASS: >=20% reduction achieved, no clipping' : 
    'FAIL: need <=-20% (got ' + totalChange + '%), clipping: ' + clipped,
    { color: pass ? '#3ddc84' : '#ff6b6b', fontWeight: 'bold' });

  const report = { timestamp: new Date().toISOString(), results, totalChange, clipped };
  console.log('\nJSON for evidence:', JSON.stringify(report, null, 2));
  
  return report;
})();
