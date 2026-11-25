import io, re
p = "agent_portal.py"
L = io.open(p, encoding="utf-8").read().splitlines(keepends=True)
out, i = [], 0
while i < len(L):
    if "/api/gpu" in L[i] or "_gfit" in L[i]:
        while i < len(L) and ("/api/gpu" in L[i] or "_gfit" in L[i]):
            i += 1
        continue
    out.append(L[i]); i += 1
s = "".join(out)
mg = re.search(r'^( *)elif p == "/api/models":', s, re.M)
ind = mg.group(1); a1 = mg.start()
getb = (ind + 'elif p == "/api/gpu/requests":\n'
        + ind + '    import portal.gpu_fit as _gfit\n'
        + ind + '    return self._json(200, {"pending": _gfit.pending_requests(), "all": _gfit._read_requests()[-30:]})\n')
s = s[:a1] + getb + s[a1:]
pm = re.search(r'^( *)m = re\.match\(r"\^/api/agents', s, re.M)
ind2 = pm.group(1); a2 = pm.start()
postb = (ind2 + 'if p == "/api/gpu/request":\n'
         + ind2 + '    import portal.gpu_fit as _gfit\n'
         + ind2 + '    rec = _gfit.request_dual_gpu(body.get("agent") or "?", body.get("model") or "")\n'
         + ind2 + '    return self._json(200, {"ok": True, "request": rec})\n'
         + ind2 + 'if p == "/api/gpu/fulfill":\n'
         + ind2 + '    import portal.gpu_fit as _gfit\n'
         + ind2 + '    hit = _gfit.fulfill_request(int(body.get("ts") or 0))\n'
         + ind2 + '    return self._json(200, {"ok": bool(hit), "hit": hit})\n')
s = s[:a2] + postb + s[a2:]
io.open(p, "w", encoding="utf-8", newline="").write(s)
import py_compile
try:
    py_compile.compile(p, doraise=True); print("FIXED")
except Exception as e:
    print("ERR", str(e).splitlines()[-1][:60])