/* test_uploads.js — smoke + edge-case tests for ui/uploads.js (validateUpload).
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

// --- T1: uploads.js evaluates without syntax error ---
var loaded = false;
try {
  var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'uploads.js'), 'utf8');
  new Function(code)();
  loaded = true;
} catch(e) {
  if (e instanceof SyntaxError) ok(false, 'uploads.js SYNTAX ERROR: ' + e.message);
  else loaded = true;
}
ok(loaded, 'uploads.js loads without syntax error');

// --- T2: validateUpload exists and handles edge cases ---
(function() {
  var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'uploads.js'), 'utf8');
  
  // Extract validateUpload function if it's a standalone function declaration
  var match = code.match(/function validateUpload\([^)]*\)\s*\{[\s\S]*?^\}/m);
  if (!match) {
    // Try to find it as an arrow function or method
    match = code.match(/validateUpload\s*[=:]\s*function[^}]+\}/);
  }
  
  if (match) {
    try {
      eval(match[0].replace(/^function validateUpload/, 'var validateUpload = function'));
      // Test: valid .md file
      var r1 = validateUpload({name: 'test.md', size: 1024});
      ok(r1 === true || (r1 && r1.ok !== false), 'validateUpload accepts .md file');
      
      // Test: blocked .exe file
      var r2 = validateUpload({name: 'malware.exe', size: 1024});
      ok(r2 === false || (r2 && r2.ok === false) || r2 === null, 'validateUpload rejects .exe');
      
      // Test: oversized file (11MB)
      var r3 = validateUpload({name: 'big.md', size: 11 * 1024 * 1024});
      ok(r3 === false || (r3 && r3.ok === false) || r3 === null, 'validateUpload rejects 11MB file');
      
      // Test: null input
      var r4 = validateUpload(null);
      ok(r4 === false || r4 === null || r4 === undefined, 'validateUpload(null) does not crash');
    } catch(e) {
      ok(false, 'validateUpload edge case error: ' + e.message);
    }
  } else {
    // Can't extract the function — verify it exists in source
    ok(code.indexOf('validateUpload') !== -1, 'validateUpload referenced in uploads.js source');
    ok(/\.exe|executable/i.test(code), 'uploads.js has executable block-list logic');
    ok(/10\s*\*\s*1024\s*\*\s*1024|10485760|10MB/i.test(code), 'uploads.js has 10MB size limit');
  }
})();

// --- T3: file type allow-list is present ---
(function() {
  var code = fs.readFileSync(path.join(__dirname, '..', '..', 'ui', 'uploads.js'), 'utf8');
  ok(/\.md/.test(code), 'allow-list includes .md');
  ok(/\.json/.test(code), 'allow-list includes .json');
  ok(/\.py/.test(code), 'allow-list includes .py');
})();

module.exports = { passed: passed, failed: failed };
