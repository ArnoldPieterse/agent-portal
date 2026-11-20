/* test_api_client.js — smoke + edge-case tests for ui/api-client.js (UMD, no DOM needed).
 * Run via: node memory/builder/ui-tests/run.js
 */
"use strict";
var path = require('path');
var ac = require(path.join(__dirname, '..', '..', 'ui', 'api-client.js'));

var passed = 0, failed = 0;
function ok(cond, msg) {
  if (cond) { passed++; console.log('  PASS ' + msg); }
  else { failed++; console.error('  FAIL ' + msg); }
}

// --- T1: module exports expected shape ---
ok(typeof ac.get === 'function', 'exports .get');
ok(typeof ac.post === 'function', 'exports .post');
ok(typeof ac.put === 'function', 'exports .put');
ok(typeof ac.del === 'function' || typeof ac.delete === 'function', 'exports .del or .delete');
ok(typeof ac._core === 'object', 'exports ._core (test hook)');

// --- T2: backoff delay is monotonic and capped ---
(function() {
  var core = ac._core;
  var d0 = core.backoffDelay(0, {baseDelayMs:100, maxDelayMs:1000}, function(){return 0;});
  var d1 = core.backoffDelay(1, {baseDelayMs:100, maxDelayMs:1000}, function(){return 0;});
  var d2 = core.backoffDelay(2, {baseDelayMs:100, maxDelayMs:1000}, function(){return 0;});
  ok(d0 === 100 && d1 === 200 && d2 === 400, 'backoff doubles correctly');
  var d9 = core.backoffDelay(9, {baseDelayMs:100, maxDelayMs:1000}, function(){return 0;});
  ok(d9 === 1000, 'backoff capped at maxDelayMs');
})();

// --- T3: cache TTL semantics ---
(function() {
  var core = ac._core;
  var m = new Map();
  core.cacheSet(m, 'k', {a:1}, 30000, 1000);
  ok(core.cacheGet(m, 'k', 15000) && core.cacheGet(m,'k',15000).a === 1, 'cache hit within TTL');
  ok(core.cacheGet(m, 'k', 31001) === null, 'cache miss after TTL expiry');
})();

// --- T4: edge cases — null/empty/oversized inputs to backoffDelay ---
(function() {
  var core = ac._core;
  // null opts -> should use defaults without crashing
  var d = core.backoffDelay(0, null, function(){return 0;});
  ok(typeof d === 'number' && d > 0, 'backoffDelay(null opts) returns positive number');
  // attempt=0 with zero base
  var d2 = core.backoffDelay(0, {baseDelayMs:0, maxDelayMs:100}, function(){return 0;});
  ok(d2 === 0, 'backoffDelay with baseDelayMs=0 returns 0');
})();

// --- T5: cacheSet/cacheGet with empty/oversized data ---
(function() {
  var core = ac._core;
  var m = new Map();
  // empty object
  core.cacheSet(m, 'empty', {}, 30000, 1000);
  ok(core.cacheGet(m, 'empty', 2000) !== null, 'cache stores empty object');
  // oversized string (1MB)
  var big = 'x'.repeat(1024 * 1024);
  core.cacheSet(m, 'big', {data: big}, 30000, 1000);
  var hit = core.cacheGet(m, 'big', 2000);
  ok(hit && hit.data.length === 1048576, 'cache handles 1MB payload');
})();

module.exports = { passed: passed, failed: failed };
