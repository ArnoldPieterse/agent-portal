import subprocess, time, json, os

p = subprocess.Popen(['python', 'memory/verifier/regression_daemon.py'],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(2)  # let daemon initialize and capture baseline mtime

# Touch the file to simulate an edit
os.utime('agent_portal.py', (time.time() + 1, time.time() + 1))

detected = False
for i in range(10):
    time.sleep(3)
    lines = [json.loads(l) for l in open('memory/verifier/regression-daemon-log.jsonl') if l.strip()]
    last = lines[-1]
    if 'mtime' in last.get('trigger', ''):
        detected = True
        print(f'DETECTED at poll {i+1}: trigger={last["trigger"]} result={last.get("result")} ts={last.get("ts")}')
        break

p.terminate()
p.wait(timeout=5)
print(f'Goal 1 auto-trigger proof: {"PASS" if detected else "FAIL"}')
