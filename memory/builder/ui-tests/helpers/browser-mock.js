/* browser-mock.js — minimal browser environment for loading ui/*.js in Node.
 * Usage: require('./helpers/browser-mock').install() before eval'ing a ui script.
 */
"use strict";

function install(overrides) {
  overrides = overrides || {};

  // --- DOM stubs ---
  function makeEl(tag) {
    var el = {
      tagName: (tag || 'div').toUpperCase(),
      children: [],
      style: {},
      classList: { add:function(){}, remove:function(){}, contains:function(){return false;} },
      dataset: {},
      innerHTML: '',
      textContent: '',
      value: '',
      disabled: false,
      hidden: false,
      appendChild: function(c){ this.children.push(c); return c; },
      prepend: function(c){ this.children.unshift(c); },
      remove: function(){},
      querySelector: function(){ return makeEl('div'); },
      querySelectorAll: function(){ return []; },
      addEventListener: function(){},
      removeEventListener: function(){},
      setAttribute: function(){},
      getAttribute: function(){ return null; },
      focus: function(){},
      blur: function(){},
      click: function(){},
      scrollIntoView: function(){},
      requestAnimationFrame: function(cb){ return 0; },
    };
    return el;
  }

  var document = {
    getElementById: function(id){ return makeEl('div'); },
    getElementsByClassName: function(){ return []; },
    querySelector: function(){ return makeEl('div'); },
    querySelectorAll: function(){ return []; },
    createElement: function(tag){ return makeEl(tag); },
    createTextNode: function(t){ return { textContent: t }; },
    addEventListener: function(){},
    removeEventListener: function(){},
    body: makeEl('body'),
    documentElement: makeEl('html'),
    head: makeEl('head'),
  };

  var window = {
    document: document,
    addEventListener: function(){},
    removeEventListener: function(){},
    setTimeout: overrides.setTimeout || function(cb, ms){ return setTimeout(cb, ms); },
    clearTimeout: function(){},
    setInterval: overrides.setInterval || function(cb, ms){ return setInterval(cb, ms); },
    clearInterval: function(){},
    requestAnimationFrame: function(cb){ return 0; },
    cancelAnimationFrame: function(){},
    location: { href: 'http://localhost:8099/', search: '', hash: '' },
    localStorage: {
      _data: {},
      getItem: function(k){ return this._data[k] || null; },
      setItem: function(k,v){ this._data[k]=String(v); },
      removeItem: function(k){ delete this._data[k]; },
    },
    fetch: overrides.fetch || function(){ return Promise.resolve({ ok:true, status:200, json:function(){return Promise.resolve({});} }); },
    navigator: { onLine: true, userAgent: 'node-test' },
    performance: { now: function(){ return Date.now(); } },
    console: console,
  };
  window.window = window; // self-reference
  window.self = window;

  // --- globals ---
  global.window = window;
  global.document = document;
  global.navigator = window.navigator;
  global.fetch = window.fetch;
  global.self = window;
  global.requestAnimationFrame = window.requestAnimationFrame;
  global.cancelAnimationFrame = window.cancelAnimationFrame;

  return { window: window, document: document };
}

module.exports = { install: install };
