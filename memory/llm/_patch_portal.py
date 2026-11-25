import io, importlib.util as ilu
spec = ilu.spec_from_file_location("gfc", "portal/gpu_fit.py")
_m = ilu.module_from_spec(spec); spec.loader.exec_module(_m)
names = [n for n in ("pending_requests", "_read_requests", "request_dual_gpu", "fulfill_request") if hasattr(_m, n)]
p = "agent_portal.py"; s = io.open(p, encoding="utf-8").read()
def indent_of(anchor):
    i = s.find(anchor)
    assert i >= 0, "anchor missing: " + anchor[:40]
    ls = s.rfind("\n", 0, i) + 1
    return i, len(s[ls:i]) - len(s[ls:i].lstrip())
# GET route: elif chained right before /api/models
a = 'elif p == "/api/models":'
i, ind = indent_of(a)
sp = " " * ind
get_body = sp + 'elif p == "/api/gpu/requests":\n' + sp + "    import portal.gpu_fit as _gfit\n"
if "pending_requests" in names:
    get_body += sp + '    return self._json(200, {"pending": _gfit.pending_requests(), "all": _gfit._read_requests()[-30:]})\n'
else:
    get_body += sp + '    return self._json(200, {"pending": [], "all": _gfit._read_requests()[-30:]})\n'
s = s[:i] + get_body + s[i:]
# POST routes: standalone ifs before the agents/(.+) match line
a2 = 'm = re.match(r"^/api/agents/(.+)$", p)'
i2, ind2 = indent_of(a2)
sp2 = " " * ind2
post_body = (sp2 + 'if p == "/api/gpu/request":\n' + sp2 + "    import portal.gpu_fit as _gfit\n"
             + sp2 + '    rec = _gfit.request_dual_gpu(body.get("agent") or "?", body.get("model") or "")\n'
             + sp2 + '    return self._json(200, {"ok": True, "request": rec})\n'
             + sp2 + 'if p == "/api/gpu/fulfill":\n' + sp2 + "    import portal.gpu_fit as _gfit\n"
             + sp2 + '    hit = _gfit.fulfill_request(int(body.get("ts") or 0))\n'
             + sp2 + '    return self._json(200, {"ok": bool(hit), "hit": hit})\n')
s = s[:i2] + post_body + s[i2:]
io.open(p, "w", encoding="utf-8").write(s)
print("PATCHED", names)