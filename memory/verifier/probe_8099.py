#!/usr/bin/env python3
"""Verifier probe: is portal :8099 reachable from this host? Latency per endpoint."""
import urllib.request, time

def get(url, timeout=10):
    t0 = time.perf_counter()
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        body = r.read()
        return (r.status, round((time.perf_counter() - t0) * 1000, 1), len(body))
    except Exception as e:
        return "ERR:" + repr(e)

for name, url in [
    ("portal_health", "http://localhost:8099/api/health"),
    ("fleet_status", "http://localhost:8099/api/fleet/status"),
    ("goals_api", "http://localhost:8099/api/goals"),
    ("llm_models", "http://localhost:8099/api/models"),
]:
    res = get(url)
    print(name, res if res else "FAIL")
