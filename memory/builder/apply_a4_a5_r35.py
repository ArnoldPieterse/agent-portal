# Builder r35 - hash-gated one-shot apply of A4 (Hunk A JS + Hunk B markup/CSS) + A5 (token split)
# Spec: memory/designer/panel-discipline-r20.md (A4/A4b), memory/designer/a5-send-contrast-hunk-r28.md (A5)
# Gate: base must be 67,681 B / md5 9c6b08e3d98355e632a72cb871d5b60d (Verifier r34 canonical ruling).
import hashlib, sys

BASE_MD5 = "9c6b08e3d98355e632a72cb871d5b60d"
raw = open("index.html", "rb").read()
if len(raw) != 67681 or hashlib.md5(raw).hexdigest() != BASE_MD5:
    sys.exit(f"GATE FAIL: size={len(raw)} md5={hashlib.md5(raw).hexdigest()} - refusing to apply")
print("GATE PASS: base 67,681 B /", BASE_MD5)

def rep(b: bytes, old: bytes, new: bytes, tag: str) -> bytes:
    n = b.count(old)
    if n != 1:
        sys.exit(f"ANCHOR FAIL [{tag}]: expected exactly 1 occurrence, found {n}")
    return b.replace(old, new)

# ---------- A5 (4 anchors, byte-exact per designer r28 spec) ----------
raw = rep(raw, b"--acc:#4f8cff;--ok:#3ddc84",
             b"--acc:#4f8cff;--acc-strong:#2f6fe0;--ok:#3ddc84", "A5-A token")
raw = rep(raw, b".seg button.on{background:var(--acc);color:#fff}",
             b".seg button.on{background:var(--acc-strong);color:#fff}", "A5-B seg")
raw = rep(raw, b"#send{background:var(--acc);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}",
             b"#send{background:var(--acc-strong);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}", "A5-C send")
raw = rep(raw, b".btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}",
             b".btn.pri{background:var(--acc-strong);border-color:var(--acc-strong);color:#fff}", "A5-D pri")
print("A5 applied (4/4 anchors)")

# ---------- A4 Hunk B part 1: CSS - modeBar position:relative + one new #panelDock rule ----------
MB_OLD = b"#modeBar{display:flex;gap:8px;padding:8px 14px;border-bottom:1px solid var(--line);align-items:center;background:var(--panel)}"
MB_NEW = (b"#modeBar{position:relative;display:flex;gap:8px;padding:8px 14px;border-bottom:1px solid var(--line);"
          b"align-items:center;background:var(--panel)}\r\n"
          b"#panelDock{position:absolute;top:100%;left:0;right:0;z-index:30;display:flex;flex-direction:column}")
raw = rep(raw, MB_OLD, MB_NEW, "A4-B css modeBar")
print("A4-B css applied")

# ---------- A4 Hunk B part 2: move the four panel divs inside #modeBar as #panelDock ----------
text = raw.decode("utf-8")
lines = text.split("\n")
i_act = lines.index("    <div id=\"actPanel\">\r")          # L188
i_msgs = lines.index("    <div id=\"msgs\"></div>\r")        # L216
panel_lines = lines[i_act:i_msgs]                           # L188..L215 (28 lines)
assert panel_lines[-1] == "    </div>\r", f"filesPanel close mismatch: {panel_lines[-1]!r}"
i_mbclose = i_act - 1                                        # L187 modeBar closing </div>
assert lines[i_mbclose] == "    </div>\r", f"modeBar close mismatch: {lines[i_mbclose]!r}"
assert 'id="stopBtn"' in lines[i_mbclose - 1], "stopBtn not immediately before modeBar close"
dock = ["      <div id=\"panelDock\">\r"] + panel_lines + ["      </div>\r"]
new_lines = lines[:i_mbclose] + dock + lines[i_mbclose:i_act] + lines[i_msgs:]
text = "\n".join(new_lines)
print(f"A4-B markup applied: moved {len(panel_lines)} panel lines into #panelDock inside #modeBar")

# ---------- A4 Hunk A: JS insert after filesRefresh anchor line, before </script> ----------
js_block = """// ---- A4 panel discipline (designer r20/r21): one-open-at-a-time + outside-click-close ----
const panelToggles={
  act:{btn:$("actBtn"),panel:$("actPanel")},
  fleet:{btn:$("fleetBtn"),panel:$("fleetPanel")},
  ops:{btn:$("opsBtn"),panel:$("opsPanel")},
  files:{btn:$("filesBtn"),panel:$("filesPanel")}
};
function panelClose(k){const t=panelToggles[k]; if(t&&t.panel.classList.contains("open"))t.btn.click();} // owning handler runs its own cleanup (actTimer/fleetTimer)
document.addEventListener("click",e=>{
  for(const k in panelToggles){
    const t=panelToggles[k];
    if(!t.panel.classList.contains("open"))continue;
    if(t.btn.contains(e.target)||t.panel.contains(e.target))continue;
    panelClose(k);
  }
});"""
anchor = b'$("filesRefresh").onclick=filesLoad;\r'
insertion = anchor + b"\r\n" + js_block.encode("utf-8").replace(b"\n", b"\r\n") + b"\r"
raw2 = text.encode("utf-8")
raw2 = rep(raw2, anchor, insertion, "A4-A js anchor")
print("A4-A js applied")

# ---------- post-apply verification ----------
out = raw2
open("index.html", "wb").write(out)
m = hashlib.md5(out).hexdigest()
lf = out.count(b"\n"); crlf = out.count(b"\r\n")
checks = {
  "size": len(out),
  "md5": m,
  "crlf_consistent": lf == crlf,
  "panelToggles": out.count(b"panelToggles"),
  "panelClose": out.count(b"panelClose"),
  "acc-strong_count": out.count(b"--acc-strong"),          # spec fingerprint: exactly 5
  "panelDock_css": b"#panelDock{position:absolute;top:100%;left:0;right:0;z-index:30;display:flex;flex-direction:column}" in out,
  "modeBar_relative": b"#modeBar{position:relative;" in out,
}
# DOM order: stopBtn < panelDock-open < actPanel < filesPanel-close < panelDock-close < modeBar-close < msgs
order = [out.index(b'id="stopBtn"'), out.index(b'<div id="panelDock">'), out.index(b'<div id="actPanel">'),
         out.rindex(b'</div>', 0, out.index(b'<div id="msgs">')), out.index(b'<div id="msgs">')]
checks["dom_order_ok"] = order == sorted(order)
# inserted JS byte-exact vs spec
spec_js = js_block.encode("utf-8").replace(b"\n", b"\r\n")
checks["js_byte_exact"] = spec_js in out
for k, v in checks.items(): print(f"  {k}: {v}")
ok = (checks["crlf_consistent"] and checks["panelToggles"] >= 1 and checks["panelClose"] >= 2
      and checks["acc-strong_count"] == 5 and checks["panelDock_css"] and checks["modeBar_relative"]
      and checks["dom_order_ok"] and checks["js_byte_exact"])
print("APPLY OK - new canonical candidate:", len(out), "B /", m) if ok else sys.exit("POST-CHECK FAIL")
