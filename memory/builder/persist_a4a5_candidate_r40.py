# Builder r40 - persist authoritative A4+A5 candidate + transform as NEW shared files
# Closes Verifier r39 gate: no seat carried bytes 45323d09 or the apply script.
# Method: run the UNMODIFIED authoritative script (root apply_a4_a5_r35.py) in a sandboxed
# temp cwd where index.html := the preserved .bak base. No root writes anywhere.
import hashlib, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # shared folder root
SCRIPT = os.path.join(ROOT, "apply_a4_a5_r35.py")
BAK    = os.path.join(ROOT, "index.html.pre-a4a5-r35.bak")
OUT    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_html_a4a5_candidate_45323d09.html")
SCRIPT_COPY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apply_a4_a5_r35.py")

EXPECT_MD5 = "45323d09717ac3a9dc0e098015863d81"
EXPECT_SIZE = 68633
BASE_MD5 = "9c6b08e3d98355e632a72cb871d5b60d"

def md5(p):
    with open(p, "rb") as f: return hashlib.md5(f.read()).hexdigest()

# 1) gate the inputs
assert os.path.getsize(SCRIPT) == 5949 and md5(SCRIPT) == "a20fc8d0cf9fdd8d0f1c73b558c63b89", "script pin drift"
assert os.path.getsize(BAK) == 67681 and md5(BAK) == BASE_MD5, "base .bak not canonical"

# 2) sandboxed run of the UNMODIFIED script (it reads/writes ./index.html in cwd)
tmp = tempfile.mkdtemp(prefix="a4a5_r40_")
shutil.copyfile(BAK, os.path.join(tmp, "index.html"))
r = subprocess.run([sys.executable, SCRIPT], cwd=tmp, capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    print(r.stderr); sys.exit("SANDBOX RUN FAILED")

# 3) persist candidate + script copy as NEW files (new files propagate; root untouched)
shutil.copyfile(os.path.join(tmp, "index.html"), OUT)
shutil.copyfile(SCRIPT, SCRIPT_COPY)
shutil.rmtree(tmp)

# 4) verify persisted bytes
out = open(OUT, "rb").read()
m = hashlib.md5(out).hexdigest()
checks = {
  "size": len(out),
  "md5": m,
  "md5_matches_claimed_pin": m == EXPECT_MD5 and len(out) == EXPECT_SIZE,
  "crlf_consistent": out.count(b"\n") == out.count(b"\r\n"),
  "acc-strong_count": out.count(b"--acc-strong"),
  "panelToggles": out.count(b"panelToggles"),
  "panelClose": out.count(b"panelClose"),
  "script_copy_md5": md5(SCRIPT_COPY),
}
order = [out.index(b'id="stopBtn"'), out.index(b'<div id="panelDock">'), out.index(b'<div id="actPanel">'),
         out.rindex(b'</div>', 0, out.index(b'<div id="msgs">')), out.index(b'<div id="msgs">')]
checks["dom_order_ok"] = order == sorted(order)
for k, v in checks.items(): print(f"  {k}: {v}")
assert checks["md5_matches_claimed_pin"], "candidate does NOT match claimed pin 45323d09 - STOP"
assert checks["crlf_consistent"] and checks["acc-strong_count"] == 5 and checks["dom_order_ok"]
print(f"PERSIST OK: {os.path.relpath(OUT, ROOT).replace(os.sep,'/')} = {len(out)} B / {m}")
print(f"PERSIST OK: {os.path.relpath(SCRIPT_COPY, ROOT).replace(os.sep,'/')} = {os.path.getsize(SCRIPT_COPY)} B / {checks['script_copy_md5']}")
