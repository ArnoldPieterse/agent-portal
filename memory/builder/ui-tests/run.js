/* run.js — UI Module Test Suite runner.
 * Usage: node memory/builder/ui-tests/run.js
 * Runs all 5 test files, reports pass/fail summary, exits non-zero on any failure.
 * Acceptance (Goal #9): all 5 pass; a deliberate syntax break in core.js is caught; run time <10s.
 */
"use strict";
var path = require('path');
var startTime = Date.now();

var TESTS = [
  'test_api_client.js',
  'test_state.js',
  'test_core.js',
  'test_components.js',
  'test_uploads.js',
];

var totalPassed = 0, totalFailed = 0;
var failures = [];

console.log('=== UI Module Test Suite ===');
console.log('Started: ' + new Date().toISOString() + '\n');

TESTS.forEach(function(file) {
  var filePath = path.join(__dirname, file);
  console.log('--- ' + file + ' ---');
  try {
    // Clear require cache so each test gets fresh module state
    delete require.cache[require.resolve(filePath)];
    var result = require(filePath);
    totalPassed += (result.passed || 0);
    totalFailed += (result.failed || 0);
    if (result.failed > 0) failures.push(file);
  } catch(e) {
    totalFailed++;
    failures.push(file + ' (THREW: ' + e.message + ')');
    console.error('  THREW: ' + e.message);
    console.error(e.stack ? e.stack.split('\n').slice(0,3).join('\n') : '');
  }
  console.log('');
});

var elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
console.log('=== SUMMARY ===');
console.log('Passed: ' + totalPassed);
console.log('Failed: ' + totalFailed);
console.log('Time:   ' + elapsed + 's');

if (failures.length > 0) {
  console.error('\nFailing files: ' + failures.join(', '));
  process.exit(1);
} else {
  console.log('\nAll tests passed. ✓');
  if (parseFloat(elapsed) >= 10) {
    console.warn('WARNING: run time exceeded 10s SLO (' + elapsed + 's)');
  }
  process.exit(0);
}
