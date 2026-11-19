#!/usr/bin/env python3
"""Static gate for ui/api-client.js (runs on hosts WITHOUT a JS engine).
Checks: balanced delimiters, all /api/* endpoints present, retry+cache core tokens,
UMD export + browser global, and module size < 500 lines.
Exit 0 = PASS. The behavioral acceptance test is memory/builder/test_api_client.js (node).
"""
import re, sys

SRC = "ui/api-client.js"
text = open(SRC, encoding="utf-8").read()
lines = text.splitlines()
errs = []

# 1) balanced delimiters (string/comment aware)
def balance(s):
    stack=[]; pairs={")":"(","]":"[","}":"{"}; i=0; n=len(s)
    in_s=None; esc=False
    while i<n:
        c=s[i]
        if in_s:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c==in_s: in_s=None
            i+=1; continue
        if c in ("'","\""): in_s=c; i+=1; continue
        if c=="/" and i+1<n and s[i+1]=="/":
            j=s.find("\n",i); i=n if j<0 else j; continue
        if c=="/" and i+1<n and s[i+1]=="*":
            j=s.find("*/",i+2); i=n if j<0 else j+2; continue
        if c in "({[": stack.append(c)
        elif c in ")]}":
            if not stack or stack.pop()!=pairs[c]: return f"unbalanced {c!r} at offset {i}"
        i+=1
    return None if not stack else f"unclosed {stack[-1]!r}"
b=balance(text)
if b: errs.append("delimiter balance: "+b)

# 2) every endpoint path must be present (matches the fetch() map in core.js/uploads.js/fleet_*)
endpoints = ["/api/agents","/api/chat","/api/file?path=","/api/git","/api/ops",
             "/api/merge-queue","/api/merge","/api/todo/prune","/api/group-run",
             "/api/run-events?run=","/api/uploads","/api/goals","/api/goals/history",
             "/api/memory-health","/api/health/fleet","/api/fleet","/api/fleet/status"]
for ep in endpoints:
    if ep not in text: errs.append(f"missing endpoint wrapper path: {ep}")

# 3) core tokens (retry + cache + UMD)
tokens = ["backoffDelay","cacheGet","cacheSet","runWithRetry","maxRetries",
          "baseDelayMs","ttlMs","module.exports","apiClient","ApiError"]
for t in tokens:
    if t not in text: errs.append(f"missing core token: {t}")

# 4) module size rule (<500 lines per JS file)
if len(lines) >= 500: errs.append(f"module too large: {len(lines)} lines (>=500)")

print(f"[gate] ui/api-client.js: {len(lines)} lines, endpoints={sum(1 for e in endpoints if e in text)}/{len(endpoints)}")
if errs:
    print("FAIL:"); [print("  -",e) for e in errs]; sys.exit(1)
print("PASS: static gate (retry core + cache core + all endpoint wrappers + UMD/global + <500 lines)")
