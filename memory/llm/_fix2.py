import io, re
p = "agent_portal.py"
s = io.open(p, encoding="utf-8").read()
L = s.splitlines(keepends=True)
out = [l for l in L if "/api/gpu" not in l and "_gfit" not in l]
s = "".join(out)
a1 = re.search(r'^( *)elif p == "/api/run-events":', s, re.M)
if a1:
    ind = a1.group(1)
    get = (ind + 'elif p == "/api/gpu/requests":\n'
           + ind + '    import portal.gpu_fit as _gfit\n'
           + ind + '    return self._json(200, {"pending": _gfit.pending_requests(), "all": _gfit._read_requests()[-30:]})\n')
    s = s[:a1.start()] + get + s[a1.start():]
else:
    print("ERR no run-events anchor")
a2 = re.search(r'^( *)m = re\.match\(r"^/api/agents/', s, re.M)
if a2:
    ind2 = a2.group(1)
    post = (ind2 + 'if p == "/api/gpu/request":\n'
            + ind2 + '    import portal.gpu_fit as _gfit\n'
            + ind2 + '    rec = _gfit.request_dual_gpu(body.get("agent") or "?", body.get("model") or "")\n'
            + ind2 + '    return self._json(200, {"ok": True, "request": rec})\n'
            + ind2 + 'if p == "/api/gpu/fulfill":\n'
            + ind2 + '    import portal.gpu_fit as _gfit\n'
            + ind2 + '    hit = _gfit.fulfill_request(int(body.get("ts") or 0))\n'
            + ind2 + '    return self._json(200, {"ok": bool(hit), "hit": hit})\n')
    s = s[:a2.start()] + post + s[a2.start():]
else:
    print("ERR no agents anchor")
io.open(p, "w", encoding="utf-8").write(s)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("COMPILE OK")
except Exception as e:
    print("ERR", str(e).splitlines()[-1][:70])