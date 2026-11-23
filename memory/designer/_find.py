
import pathlib
p = pathlib.Path("ui/cockpit.js")
t = p.read_text(encoding="utf-8")
for l in t.splitlines():
    if "ckrbRun" in l or "ckrbAbort" in l:
        print(repr(l))
