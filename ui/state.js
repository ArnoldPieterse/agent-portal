// ui/state.js — single portal state store with subscribe/notify (plain script, no ES modules)
// Goal 6: State Management Refactor (increment 1)
// Loaded before core.js; exposes window.State.

(function(){
  const _store = {};
  const _listeners = {}; // key -> Set<fn>

  function getState(key) {
    if (key === undefined) return Object.assign({}, _store);
    return _store[key];
  }

  function setState(key, value, opts) {
    opts = opts || {};
    var prev = _store[key];
    if (prev === value && !opts.force) return;
    _store[key] = value;
    var set = _listeners[key];
    if (set) set.forEach(function(fn){ try{ fn(value, prev, key); }catch(e){ console.error('[state]', e); } });
    var wild = _listeners['*'];
    if (wild) wild.forEach(function(fn){ try{ fn(value, prev, key); }catch(e){ console.error('[state:*]', e); } });
  }

  function subscribe(key, fn) {
    if (!_listeners[key]) _listeners[key] = new Set();
    _listeners[key].add(fn);
    return function(){ _listeners[key].delete(fn); };
  }

  function seedState(obj) {
    for (var k in obj) if (obj.hasOwnProperty(k)) _store[k] = obj[k];
  }

  window.State = { getState: getState, setState: setState, subscribe: subscribe, seedState: seedState };
})();
