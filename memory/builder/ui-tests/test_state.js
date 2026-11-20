/* test_state.js — smoke + edge-case tests for ui/state.js.
 * Requires browser-mock (window global). Run via: node memory/builder/ui-tests/run.js
 */
"use strict";
var fs = require('fs'), path = require('path');
var mock = require('./helpers/browser-mock');
mock.install();

// Load state.js in the mocked window context
var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'state.js'), 'utf8');
eval(code);

var passed = 0, failed = 0;
function ok(cond, msg) {
  if (cond) { passed++; console.log('  PASS ' + msg); }
  else { failed++; console.error('  FAIL ' + msg); }
}

// --- T1: window.State exists with expected methods ---
ok(typeof window.State === 'object', 'window.State is object');
ok(typeof window.State.getState === 'function', 'State.getState is function');
ok(typeof window.State.setState === 'function', 'State.setState is function');
ok(typeof window.State.subscribe === 'function', 'State.subscribe is function');
ok(typeof window.State.seedState === 'function', 'State.seedState is function');

// --- T2: basic get/set roundtrip ---
window.State.setState('testKey', {value: 42});
ok(window.State.getState('testKey').value === 42, 'setState/getState roundtrip');

// --- T3: subscribe receives value + prev ---
var received = null;
var unsub = window.State.subscribe('subKey', function(val, prev) { received = {val: val, prev: prev}; });
window.State.setState('subKey', 'first');
ok(received && received.val === 'first' && received.prev === undefined, 'subscribe fires with val + prev=undefined');
window.State.setState('subKey', 'second');
ok(received.val === 'second' && received.prev === 'first', 'subscribe receives updated prev');
unsub(); // cleanup

// --- T4: wildcard subscribe ---
var wildHits = [];
var unsubW = window.State.subscribe('*', function(val, prev, key) { wildHits.push(key); });
window.State.setState('wildA', 1);
window.State.setState('wildB', 2);
ok(wildHits.length === 2 && wildHits[0] === 'wildA' && wildHits[1] === 'wildB', 'wildcard * receives all keys');
unsubW();

// --- T5: edge cases — null, empty array, oversized string ---
window.State.setState('nullVal', null);
ok(window.State.getState('nullVal') === null, 'stores null without error');

window.State.setState('emptyArr', []);
ok(Array.isArray(window.State.getState('emptyArr')) && window.State.getState('emptyArr').length === 0, 'stores empty array');

var bigStr = 'A'.repeat(1024 * 1024); // 1MB
window.State.setState('bigStr', bigStr);
ok(window.State.getState('bigStr').length === 1048576, 'stores 1MB string without error');

// --- T6: getState() with no key returns full store clone ---
var full = window.State.getState();
ok(typeof full === 'object' && full !== null, 'getState() returns object (full store)');
ok(full.testKey !== undefined, 'full store contains known keys');

module.exports = { passed: passed, failed: failed };
