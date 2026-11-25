#!/usr/bin/env python3
"""One-at-a-time fleet download: Gemma 4 31B Q4_K_M (2026-11-25, Arnold directive).
Drops the GGUF straight into LM Studio's community folder so it auto-registers.
Idempotent (.done marker). Log: gemma4-download.log next to this file."""
import os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = r"C:\Users\White\.lmstudio\models\lmstudio-community\gemma-4-31B-it-Q4_K_M.gguf"
URL = ("https://huggingface.co/lmstudio-community/gemma-4-31B-it-GGUF/"
       "resolve/main/gemma-4-31B-it-Q4_K_M.gguf")
LOG = os.path.join(HERE, "gemma4-download.log")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


os.makedirs(os.path.dirname(DEST), exist_ok=True)
if os.path.exists(DEST + ".done"):
    log("already done, skipping")
    sys.exit(0)
tmp = DEST + ".part"
log("start " + URL)
req = urllib.request.Request(URL, headers={"User-Agent": "agent-portal-fleet/1.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    total = int(r.headers.get("Content-Length") or 0)
    log("content-length %d bytes" % total)
    with open(tmp, "wb") as f:
        got, last = 0, 0.0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            now = time.time()
            if now - last > 30:
                pct = (100.0 * got / total) if total else 0.0
                log("progress %d/%d MB (%.1f%%)" % (got // 1e6, total // 1e6, pct))
                last = now
os.replace(tmp, DEST)
with open(DEST + ".done", "w", encoding="utf-8") as f:
    f.write(time.strftime("%Y-%m-%dT%H:%M:%S"))
log("DONE %d bytes -> %s" % (os.path.getsize(DEST), DEST))
