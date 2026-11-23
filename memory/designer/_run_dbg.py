
import sys; sys.path.insert(0,'memory/designer')
from _js_dbg import js_scan
s = "var a=`hi ${ {n:1}.n } world`;"
print("input:", repr(s))
r = js_scan(s, _debug=True)
print("RESULT", r)
