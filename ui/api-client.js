/* ui/api-client.js — typed API client for all /api/* portal endpoints.
 * Retry (exponential backoff, max 3 retries) + TTL cache (default 30s, read-only).
 * Browser global: window.apiClient. Node test: require() returns the same object.
 * Core algorithm (backoffDelay/cacheGet/cacheSet/runWithRetry) is dependency-injected
 * so it can be exercised in-process with a stubbed fetch + sleep (see memory/builder/test_api_client.js).
 */
(function (global, factory) {
  if (typeof module === 'object' && module.exports) { module.exports = factory(); }
  else { global.apiClient = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {

  var DEFAULTS = { maxRetries: 3, baseDelayMs: 200, maxDelayMs: 2000, ttlMs: 30000 };

  function ApiError(kind, status, path, data, cause) {
    var msg = (kind === 'http' ? 'HTTP ' + status : kind) + ' error for ' + path;
    Error.call(this, msg);
    this.name = 'ApiError'; this.kind = kind; this.status = status;
    this.path = path; this.data = data; if (cause) this.cause = cause;
  }
  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;

  /* ---------- pure core (dependency-injected => testable in-process) ---------- */

  // Exponential backoff with full jitter, capped at maxDelayMs.
  function backoffDelay(attempt, opts, rng) {
    var base = (opts && opts.baseDelayMs != null) ? opts.baseDelayMs : DEFAULTS.baseDelayMs;
    var cap  = (opts && opts.maxDelayMs  != null) ? opts.maxDelayMs  : DEFAULTS.maxDelayMs;
    var exp  = Math.min(cap, base * Math.pow(2, attempt));
    var jitter = ((rng || Math.random)()) * base;
    return Math.min(cap, exp + jitter);
  }

  function cacheGet(map, key, now) {
    var e = map.get(key);
    if (!e) return null;
    if (now - e.ts > e.ttl) { map.delete(key); return null; }
    return e.data;
  }
  function cacheSet(map, key, data, ttl, now) { map.set(key, { data: data, ts: now, ttl: ttl }); }

  // Driver. deps = { fetchImpl(url,init)->Promise<ResponseLike>, sleep(ms), now(), rng(), cache:Map }.
  // Returns { data, cached, attempts }. Throws ApiError on final failure.
  async function runWithRetry(path, opts, deps) {
    var method = (opts.method || 'GET').toUpperCase();
    var maxRetries = (opts.maxRetries != null) ? opts.maxRetries : DEFAULTS.maxRetries;
    var retriable = (method === 'GET') || (opts.retry === true);

    var cacheKey = null, ttl = 0;
    if (opts.cache !== false && method === 'GET') {
      ttl = (opts.ttl != null) ? opts.ttl : DEFAULTS.ttlMs;
      if (ttl > 0) {
        cacheKey = opts.cacheKey || path;
        var hit = cacheGet(deps.cache, cacheKey, deps.now());
        if (hit != null) return { data: hit, cached: true, attempts: 0 };
      }
    }

    function parseJson(res) {
      try { return res.json ? await res.json() : null; } catch (e) { return null; }
    }

    var lastErr = null;
    for (var attempt = 0; attempt <= maxRetries; attempt++) {
      var res;
      try {
        res = await deps.fetchImpl(path, { method: method, headers: opts.headers || {}, body: opts.body, signal: opts.signal });
      } catch (netErr) {
        if (retriable && attempt < maxRetries) { lastErr = netErr; await deps.sleep(backoffDelay(attempt, opts, deps.rng)); continue; }
        throw new ApiError('network', null, path, null, netErr);
      }
      var status = res.status;
      if (!res.ok) {
        var errData = await parseJson(res);
        if (retriable && (status >= 500 || status === 429) && attempt < maxRetries) {
          lastErr = new ApiError('http', status, path, errData);
          await deps.sleep(backoffDelay(attempt, opts, deps.rng)); continue;
        }
        throw new ApiError('http', status, path, errData);
      }
      var data = await parseJson(res);
      if (cacheKey != null) cacheSet(deps.cache, cacheKey, data, ttl, deps.now());
      return { data: data, cached: false, attempts: attempt + 1 };
    }
    throw lastErr || new ApiError('network', null, path);
  }

  /* ---------- client factory ---------- */
  function createApiClient(overrides) {
    var cfg = Object.assign({}, DEFAULTS, overrides || {});
    var cache = new Map();
    var deps = {
      fetchImpl: (overrides && overrides.fetchImpl) || function (u, i) { return fetch(u, i); },
      sleep:     (overrides && overrides.sleep)     || function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); },
      now:       Date.now,
      rng:       Math.random,
      cache:     cache
    };

    async function requestFull(path, opts) {
      var o = Object.assign({ method: 'GET' }, opts);
      if (o.json != null) {
        o.headers = Object.assign({ 'Content-Type': 'application/json' }, o.headers || {});
        o.body = JSON.stringify(o.json);
        delete o.json;
      }
      return runWithRetry(path, o, deps);
    }
    function request(path, opts) {
      return requestFull(path, opts).then(function (r) { return r.data; });
    }

    var api = {
      request: request,
      requestFull: requestFull,
      clearCache: function () { cache.clear(); },
      config: cfg,
      _core: { backoffDelay: backoffDelay, cacheGet: cacheGet, cacheSet: cacheSet, runWithRetry: runWithRetry },
      _cache: cache,

      // agents
      listAgents: function () { return request('/api/agents'); },
      deleteAgent: function (id) { return request('/api/agents/' + encodeURIComponent(id), { method: 'DELETE' }); },
      // chat — long-running, no retry, no cache; supports AbortSignal
      postChat: function (payload, o) { return request('/api/chat', Object.assign({ method: 'POST', json: payload, cache: false, retry: false }, o)); },
      // files / git / ops / merge / todo
      getFile: function (p) { return request('/api/file?path=' + encodeURIComponent(p), { cache: false }); },
      getGit: function () { return request('/api/git'); },
      postGit: function (b) { return request('/api/git', { method: 'POST', json: b }); },
      getOps: function () { return request('/api/ops'); },
      getMergeQueue: function () { return request('/api/merge-queue'); },
      postMerge: function (b) { return request('/api/merge', { method: 'POST', json: b }); },
      postTodoPrune: function (b) { return request('/api/todo/prune', { method: 'POST', json: b }); },
      // uploads / runs / goals / health
      groupRun: function (b) { return request('/api/group-run', { method: 'POST', json: b }); },
      runEvents: function (run, cursor, o) { return request('/api/run-events?run=' + encodeURIComponent(run) + '&cursor=' + (cursor || 0), Object.assign({ cache: false }, o)); },
      listUploads: function () { return request('/api/uploads'); },
      getGoals: function () { return request('/api/goals'); },
      goalsHistory: function () { return request('/api/goals/history'); },
      memoryHealth: function () { return request('/api/memory-health', { cache: false }); },
      // fleet (live probes — never cached)
      fleetHealth: function () { return request('/api/health/fleet', { cache: false }); },
      fleetTopology: function () { return request('/api/fleet', { cache: false }); },
      fleetStatus: function () { return request('/api/fleet/status', { cache: false }); }
    };
    return api;
  }

  return createApiClient();
});
