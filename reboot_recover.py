# Provenance: header added 2026-11-15 by Orchestrator (Archivist goal 6 audit). Original: fleet-ops scripts (Arnold + agent legs); purpose in the docstring/comments below.
# reboot_recover.py - post-reboot bring-up for White local (portal + TCP probes of remotes)
import socket, subprocess, time, urllib.request

def tcp(h):
    try: return socket.socket().connect_ex((h, 8888)) == 0
    except Exception: return False

def http(url, t=4):
    try:
        with urllib.request.urlopen(url, timeout=t) as r: return r.status
    except Exception: return None

out = []
# portal
if http("http://127.0.0.1:8099/") == 200:
    out.append("portal=UP")
else:
    subprocess.run(["wscript.exe", r"C:\Projects\Workspace\memory\ops\launch_host.vbs"], timeout=20)  # 2026-11-23: PortalRun schtask retired; Startup-VBS launch path
    time.sleep(6)
    out.append("portal=" + ("UP" if http("http://127.0.0.1:8099/") == 200 else "STILL-DOWN"))
# local studio
out.append("studio=" + str(http("http://127.0.0.1:8888/api/health")))
# remotes
out.append("black=" + ("OPEN" if tcp("IP_BLACK") else "closed"))
out.append("pale=" + ("OPEN" if tcp("IP_PALE") else "closed"))
out.append("red=" + ("OPEN" if tcp("IP_RED") else "closed"))
line = "; ".join(out)
open("reboot_status.txt", "w").write(line + "\n")
print(line[:120])
