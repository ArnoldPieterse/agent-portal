#!/usr/bin/env python3
"""Dry-run: verify WinRM+SMB reachability to Pale and Black from Red host."""
import json, datetime, socket, http.client

HOSTS = [
    ("PALE", "IP_PALE"),
    ("BLACK", "IP_BLACK"),
]

results = []
for name, ip in HOSTS:
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": name, "ip": ip, "dry_run": True, "checks": {}
    }
    try:
        s = socket.create_connection((ip, 5985), timeout=5); s.close()
        entry["checks"]["winrm_tcp_5985"] = "PASS"
    except Exception as e:
        entry["checks"]["winrm_tcp_5985"] = f"FAIL: {e}"
    try:
        s = socket.create_connection((ip, 445), timeout=5); s.close()
        entry["checks"]["smb_tcp_445"] = "PASS"
    except Exception as e:
        entry["checks"]["smb_tcp_445"] = f"FAIL: {e}"
    try:
        conn = http.client.HTTPConnection(ip, 5985, timeout=5)
        conn.request("GET", "/wsman")
        resp = conn.getresponse()
        if resp.status in (401, 403, 405):
            entry["checks"]["winrm_http_service"] = f"PASS (HTTP {resp.status} = service alive)"
        else:
            entry["checks"]["winrm_http_service"] = f"UNEXPECTED: HTTP {resp.status}"
        conn.close()
    except Exception as e:
        entry["checks"]["winrm_http_service"] = f"FAIL: {e}"
    all_pass = all(v.startswith("PASS") for v in entry["checks"].values())
    entry["verdict"] = "DRY-RUN PASS" if all_pass else "DRY-RUN FAIL"
    results.append(entry)
    print(f"{name}: {entry['verdict']}")
    for k, v in entry["checks"].items():
        print(f"  {k}: {v}")

evidence = {
    "goal": "mechanic#4",
    "description": "Pale + Black dry-run for reboot-recovery deployment (run from Red)",
    "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "from_host": "RED",
    "results": results,
    "summary": f"{sum(1 for r in results if 'PASS' in r['verdict'])}/2 hosts dry-run PASS",
    "remaining_for_full_deploy": [
        "Install pywinrm on White (or target host)",
        "Run deploy_reboot_recovery_all.py from White with admin privileges",
        "Verify schtask FleetBootRecovery exists on all 4 hosts"
    ]
}
with open("memory/mechanic/goal4-pale-black-dryrun-2026-11-18.json", "w") as f:
    json.dump(evidence, f, indent=2)
print(f"\nEvidence: memory/mechanic/goal4-pale-black-dryrun-2026-11-18.json")
