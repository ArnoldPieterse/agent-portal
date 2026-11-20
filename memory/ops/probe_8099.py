import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:8099/api/health', timeout=5)
    print('OK status=%s' % r.status)
except Exception as e:
    import sys
    print('FAIL %s %r' % (type(e).__name__, getattr(e, 'args', e)))
