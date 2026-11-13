# reboot_launchers.py - spawn Black + Pale dual-load chains fully detached
import subprocess, os
DET = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

def det(cmd, log):
    f = open(log, "w", encoding="utf-8")
    subprocess.Popen(["python"] + cmd, stdout=f, stderr=subprocess.STDOUT,
                     creationflags=DET, close_fds=True)
    print("spawned:", " ".join(cmd[:1]), "->", log)

# Black: single script loads both + aliases + probes
det(["black_dual_load2.py"], "black_rb2.log")
# Pale: Q8 first, then Q4 alongside (sequential chain in one detached cmd)
f = open("pale_rb_chain.log", "w", encoding="utf-8")
subprocess.Popen(['cmd', '/c', 'python pale_load_q8.py > pale_rb_q8.log 2>&1 && python pale_q4s_load.py > pale_rb_q4s.log 2>&1'],
                 stdout=f, stderr=subprocess.STDOUT, creationflags=DET, close_fds=True)
print("spawned: pale chain")
