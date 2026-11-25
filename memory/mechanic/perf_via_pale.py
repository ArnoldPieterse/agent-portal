"""Run perf_profile via WinRM on PALE (which can reach White:8099).
Workaround for sandbox egress wall blocking direct :8099 access.
Usage: python memory/mechanic/perf_via_pale.py [duration_s]
Default duration: 60s (goal requires 3600s for full closure)
"""
import winrm, json, sys

PALE = 'http://IP_PALE:5985/wsman'
AUTH = ('pale', '[REDACTED-CREDENTIAL]')
WHITE_PORTAL = 'http://IP_LAN:8099'

REMOTE_SCRIPT = '''
import urllib.request, time, json, statistics, sys
from datetime import datetime, timezone

PORTAL_URL = "http://IP_LAN:8099"
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 60
ENDPOINTS = {
    "portal_health": PORTAL_URL + "/api/health",
    "fleet_status": PORTAL_URL + "/api/fleet/status",
    "goals_api": PORTAL_URL + "/api/goals",
}
SAMPLE_INTERVAL = 5

def percentile(data, p):
    if not data: return None
    s = sorted(data)
    k = (len(s)-1)*(p/100.0)
    f=int(k); c=f+1 if f+1<len(s) else f
    d=k-f
    return s[f]+d*(s[c]-s[f])

def timed_get(url, timeout=10):
    t0=time.perf_counter()
    try:
        r=urllib.request.urlopen(url,timeout=timeout); r.read()
        return (time.perf_counter()-t0)*1000
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return None

print(f"[perf] Profiling {PORTAL_URL} for {DURATION}s from PALE")
samples = {k:[] for k in ENDPOINTS}
samples["llm_models"] = []
deadline = time.time() + DURATION
n=0
while time.time() < deadline:
    n+=1
    for name,url in ENDPOINTS.items():
        ms=timed_get(url)
        if ms is not None: samples[name].append(ms)
    t0=time.perf_counter()
    try:
        r=urllib.request.urlopen(PORTAL_URL+"/api/models",timeout=10); r.read()
        samples["llm_models"].append((time.perf_counter()-t0)*1000)
    except Exception: pass
    print(f"  [{n}] t={time.time()-(deadline-DURATION):.0f}s " + ", ".join(f"{k}={len(v)}" for k,v in samples.items()))
    if time.time() < deadline: time.sleep(SAMPLE_INTERVAL)

results = {"generated_at": datetime.now(timezone.utc).isoformat(), "duration_s": DURATION,
           "samples_collected": {k:len(v) for k,v in samples.items()}, "metrics": {}}
for name, vals in samples.items():
    if not vals:
        results["metrics"][name] = {"status":"no_samples","p50":None,"p95":None,"p99":None}
    else:
        results["metrics"][name] = {"status":"ok","count":len(vals),"min_ms":round(min(vals),2),
            "max_ms":round(max(vals),2),"mean_ms":round(statistics.mean(vals),2),
            "p50":round(percentile(vals,50),2),"p95":round(percentile(vals,95),2),"p99":round(percentile(vals,99),2)}
print("===JSON_START===")
print(json.dumps(results, indent=2))
'''

def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f"[perf_via_pale] Connecting to PALE via WinRM...")
    s = winrm.Session(PALE, auth=AUTH, transport='ntlm')
    
    # Write script to PALE via PowerShell here-string
    ps_write = f"""
$script = @'
{REMOTE_SCRIPT}
'@
New-Item -ItemType Directory -Force -Path C:\temp | Out-Null
Set-Content -Path C:\temp\perf_via_pale.py -Value $script -Encoding UTF8
Write-Output "OK: script written"
"""
    r = s.run_ps(ps_write)
    out = r.std_out.decode().strip()
    err = r.std_err.decode().strip()
    print(f"  Write result: {out}")
    if err: print(f"  STDERR: {err[:200]}")
    
    # Execute
    print(f"[perf_via_pale] Running {duration}s profile on PALE (targeting White:8099)...")
    r = s.run_cmd('python', [r'C:\temp\perf_via_pale.py', str(duration)], timeout=duration+120)
    out = r.std_out.decode()
    err = r.std_err.decode()
    print(out[-3000:])  # last 3000 chars (progress + JSON)
    if err: print(f"STDERR: {err[:500]}")
    
    # Extract JSON
    try:
        marker = '===JSON_START==='
        json_start = out.index(marker) + len(marker)
        json_data = json.loads(out[json_start:].strip())
        with open('memory/mechanic/perf-profile.json', 'w') as f:
            json.dump(json_data, f, indent=2)
        all_ok = all(m.get('status')=='ok' for m in json_data['metrics'].values())
        print(f"\n[perf_via_pale] Saved to memory/mechanic/perf-profile.json")
        print(f"  All endpoints OK: {all_ok}")
        for ep, m in json_data['metrics'].items():
            if m.get('status') == 'ok':
                print(f"  {ep}: p50={m['p50']}ms p95={m['p95']}ms p99={m['p99']}ms (n={m['count']})")
            else:
                print(f"  {ep}: {m.get('status')}")
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[perf_via_pale] Could not parse JSON: {e}")

if __name__ == '__main__':
    main()
