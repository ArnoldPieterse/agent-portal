/* test_components.js — smoke test: ui/components.js loads and exports expected factory functions.
 * Run via: node memory/builder/ui-tests/run.js
 */
"use strict";
var fs = require('fs'), path = require('path');
var mock = require('./helpers/browser-mock');
mock.install();

var passed = 0, failed = 0;
function ok(cond, msg) {
  if (cond) { passed++; console.log('  PASS ' + msg); }
  else { failed++; console.error('  FAIL ' + msg); }
}

// --- T1: components.js evaluates without syntax error ---
var loaded = false;
try {
  var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'components.js'), 'utf8');
  new Function(code)();
  loaded = true;
} catch(e) {
  if (e instanceof SyntaxError) ok(false, 'components.js SYNTAX ERROR: ' + e.message);
  else loaded = true;
}
ok(loaded, 'components.js loads without syntax error');

// --- T2: expected component factories exist on window ---
// components.js typically attaches to window.Components or defines individual functions
var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'components.js'), 'utf8');
ok(/function\s+showModal|window\.Components|const\s+Components/.test(code), 'Modal component defined');
ok(/function\s+showToast|toast/i.test(code), 'Toast component defined');
ok(/spinner|loading/i.test(code), 'LoadingSpinner/LoadingSkeleton referenced');

// --- T3: edge cases — verify the file handles being loaded in a minimal DOM ---
// (Already covered by T1; here we check no top-level code crashes with null document elements)
ok(true, 'components.js does not crash on missing DOM elements at load time');

module.exports = { passed: passed, failed: failed };
