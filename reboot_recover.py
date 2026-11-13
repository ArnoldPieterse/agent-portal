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
    subprocess.run(["schtasks", "/run", "/tn", "PortalRun"], capture_output=True)
    time.sleep(6)
    out.append("portal=" + ("UP" if http("http://127.0.0.1:8099/") == 200 else "STILL-DOWN"))
# local studio
out.append("studio=" + str(http("http://127.0.0.1:8888/api/health")))
# remotes
out.append("black=" + ("OPEN" if tcp("192.168.1.99") else "closed"))
out.append("pale=" + ("OPEN" if tcp("192.168.1.39") else "closed"))
out.append("red=" + ("OPEN" if tcp("192.168.1.245") else "closed"))
line = "; ".join(out)
open("reboot_status.txt", "w").write(line + "\n")
print(line[:120])
