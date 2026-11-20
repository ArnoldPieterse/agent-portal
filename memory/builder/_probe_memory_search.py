import urllib.request as u
base = "http://127.0.0.1:8099"
paths = [
    "/api/memory/search?q=hotload&top=5",
    "/api/memory-search?q=hotload",
    "/api/memory-health",
    "/api/goals",
]
for p in paths:
    try:
        r = u.urlopen(base + p, timeout=6)
        body = r.read(240).decode("utf-8", "replace")
        print("[%s] %s" % (r.status, p))
        print("     ", body.replace(chr(10), " "))
    except Exception as e:
        print("[ERR] %s -> %r" % (p, e))
