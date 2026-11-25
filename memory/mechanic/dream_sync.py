#!/usr/bin/env python3
"""
dream_sync.py - Daily mandatory 5-minute fleet dream (2026-11-25, Arnold directive).

WHAT: Once per day at DREAM_START (default 03:30 local), ALL FOUR nodes do nothing
for WINDOW_MIN minutes. That quiescent window is used to reboot every host and to
detect stuck nodes that need more extensive recovery.

WHY ONE WINDOW FOR ALL: parallel reboots fit inside 5 minutes only because no agent
work runs on any host during the window (portal gates dispatch while ACTIVE flag is
set - see _dream_state() in agent_portal.py). Sequential reboots would take ~15 min.

SEQUENCE (crash-safe, resumable via state.json phase):
  quiesce           write ACTIVE state; portal stops dispatching turns fleet-wide
  pre_probe         probe all 4 hosts (TCP :8888 + models loaded); already-down hosts
                    are flagged STUCK_PRE (no reboot attempt - deeper recovery needed)
  reboots_issued    issue Restart-Computer in PARALLEL to up remotes (Red/Pale/Black)
  awaiting_remotes  poll each remote until :8888 opens; BOOT_TIMEOUT_S -> STUCK_POST
  models_verify     wait for boot tasks to load models (MODEL_WAIT_S); not loaded ->
                    DEGRADED + incident note (host up, model absent)
  white_reboot      verify portal healthy, then `shutdown /r /t 45` on White itself;
                    phase -> awaiting_white_boot (survives the reboot in state.json)
  awaiting_white_boot  (post-boot watch run) re-verify remotes, write report, clear flag

STUCK NODES: a host that was down before the dream (STUCK_PRE) or fails to return
within BOOT_TIMEOUT_S (STUCK_POST) gets an incident file under memory/ops/incidents/
with the deeper-recovery path (memory/ops/runbooks/host_down_response.md, recover_all.py)
and is reported in the daily report + MEMORY.md hot note. No auto-retry within the
same window (prevents reboot loops).

USAGE:
  python memory/mechanic/dream_sync.py watch          # schtask entry (every 10 min, self-gating)
  python memory/mechanic/dream_sync.py run --dry-run  # probe + report only, NO reboots
  python memory/mechanic/dream_sync.py run --force    # manual full sequence NOW (test!)
"""
import json, os, socket, subprocess, sys, time, urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))          # .../memory/mechanic
ROOT = os.path.dirname(os.path.dirname(HERE))              # AgentPortal root
DREAM_DIR = os.path.join(ROOT, "memory", "dream")
STATE = os.path.join(DREAM_DIR, "state.json")
REPORTS = os.path.join(DREAM_DIR, "reports")
INCIDENTS = os.path.join(ROOT, "memory", "ops", "incidents")

# --- configuration (Arnold may tune these) -------------------------------
DREAM_HOUR, DREAM_MIN = 3, 30      # daily start, local time
WINDOW_MIN = 5                     # mandatory do-nothing window (minutes)
GRACE_H = 4                        # catch-up if White was down at start (hours)
BOOT_TIMEOUT_S = 720               # per-remote max time to come back up
MODEL_WAIT_S = 600                 # max wait for boot tasks to load models
ACTIVE_STALE_S = 30 * 60           # ACTIVE older than this with no progress -> abandon
POLL_S = 15                        # probe poll interval

import json as _json, os as _os
try:
    _FL_TABLE = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "fleet_local.json"), encoding="utf-8")).get("hosts", {})
except Exception:
    _FL_TABLE = {}
def _fip(r):
    return (_FL_TABLE.get(r) or {}).get("ip") or ("LAN_" + r.upper())
HOSTS = {   # name: (ip, is_local) - real IPs from gitignored fleet_local.json (public-repo hygiene)
    "White": ("127.0.0.1", True),
    "Red":   (_fip("red"), False),
    "Pale":  (_fip("pale"), False),
    "Black": (_fip("black"), False),
}

# --------------------------------------------------------------------------
def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        os.makedirs(DREAM_DIR, exist_ok=True)
        with open(os.path.join(DREAM_DIR, "dream.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(st):
    os.makedirs(DREAM_DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATE)

def tcp(ip, port=8888, timeout=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ok = s.connect_ex((ip, port)) == 0
        s.close()
        return ok
    except Exception:
        return False

def models_loaded(ip):
    """True if Studio reports >=1 loaded model (same endpoint as host_reboot_verify.py)."""
    try:
        req = urllib.request.Request(f"http://{ip}:8888/api/v0/models/loaded")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        ms = data.get("models", [data.get("model", "")]) if isinstance(data, dict) else []
        return bool(ms)
    except Exception:
        return False

def probe_host(name):
    ip, local = HOSTS[name]
    up = tcp(ip)
    mdl = models_loaded(ip) if up else False
    return {"up": up, "models": mdl, "checked": datetime.now().isoformat(timespec="seconds")}

def incident(host, kind, detail):
    os.makedirs(INCIDENTS, exist_ok=True)
    p = os.path.join(INCIDENTS, f"dream-{kind}-{host.lower()}-{datetime.now():%Y%m%d}.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(f"# Dream incident: {host} {kind}\n\n"
                f"Detected by dream_sync.py at {datetime.now():%Y-%m-%d %H:%M}.\n\n"
                f"{detail}\n\n## Deeper recovery path\n"
                f"1. memory/ops/runbooks/host_down_response.md (power cycle, boot-task check)\n"
                f"2. python recover_all.py (fleet-wide recovery sweep)\n"
                f"3. If still stuck: RDP in and inspect manually (C:\\Users\\<user>)\n")
    log(f"INCIDENT {host} {kind}: {p}")
    return p

# --------------------------------------------------------------------------
def dream_start_today():
    now = datetime.now().replace(second=0, microsecond=0)
    start = now.replace(hour=DREAM_HOUR, minute=DREAM_MIN)
    if now < start:
        start -= timedelta(days=1)   # yesterday's dream missed -> catch up within grace
    return start

def in_window(now):
    start = dream_start_today()
    return start <= now <= start + timedelta(hours=GRACE_H)

def issue_reboot_remote(name):
    """Parallel-safe reboot of one remote. Returns (ok, method)."""
    ip, _ = HOSTS[name]
    user = {"Red": "Red", "Pale": "pale", "Black": "black"}.get(name, name.lower())
    # Method 1: PowerShell remoting (proven path from host_reboot_verify.py)
    ps = f'powershell -NoProfile -Command "Invoke-Command -ComputerName {ip} -Credential (New-Object PSCredential(\'{user}\',(ConvertTo-SecureString \'\' -AsPlainText -Force))) -ScriptBlock {{ Restart-Computer -Force }}"'
    try:
        r = subprocess.run(ps, shell=True, capture_output=True, text=True, timeout=40)
        if r.returncode == 0:
            return True, "powershell_reboot"
    except Exception:
        pass
    # Method 2: pywinrm shutdown (fallback)
    try:
        import winrm
        sess = winrm.Session(f"http://{ip}:5985/wsman", auth=(user, ""), transport="ntlm")
        sess.run_cmd("shutdown", ["/r", "/t", "10"])
        return True, "winrm_shutdown"
    except Exception as e:
        return False, str(e)[:120]

# --------------------------------------------------------------------------
def run_sequence(dry=False, force=False):
    now = datetime.now()
    st = {"active": True, "dry_run": dry, "started": now.isoformat(timespec="seconds"),
          "window_min": WINDOW_MIN, "phase": "quiesce", "hosts": {}, "report": None}
    for h in HOSTS:
        st["hosts"][h] = {"pre": probe_host(h), "reboot": None, "up_at": None,
                          "models_at": None, "status": "ok"}
    save_state(st)
    log(f"DREAM START (dry={dry}) window {WINDOW_MIN}min - all nodes quiesced")

    # --- pre-probe already recorded above; flag hosts that were down before the dream
    for h, hs in st["hosts"].items():
        if not hs["pre"]["up"]:
            hs["status"] = "STUCK_PRE"
            log(f"{h} was ALREADY DOWN before dream -> STUCK_PRE (deeper recovery needed)")

    if dry:
        st["phase"] = "done_dry"
        st["active"] = False
        save_state(st)
        write_report(st, note="DRY RUN - probes only, no reboots issued")
        return 0

    # --- issue reboots in PARALLEL to every remote that is up (White reboots last)
    for h in ("Red", "Pale", "Black"):
        hs = st["hosts"][h]
        if hs["status"] == "STUCK_PRE":
            continue
        ok, method = issue_reboot_remote(h)
        hs["reboot"] = {"ok": ok, "method": method, "at": datetime.now().isoformat(timespec="seconds")}
        st["phase"] = "reboots_issued"
        save_state(st)
        log(f"{h} reboot issued: ok={ok} via {method}")
        if not ok:
            hs["status"] = "REBOOT_FAILED"

    # --- wait for remotes to come back (parallel poll)
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    pending = [h for h in ("Red", "Pale", "Black")
               if st["hosts"][h]["status"] not in ("STUCK_PRE", "REBOOT_FAILED")]
    while pending and time.monotonic() < deadline:
        for h in list(pending):
            ip, _ = HOSTS[h]
            if tcp(ip, timeout=5):
                st["hosts"][h]["up_at"] = datetime.now().isoformat(timespec="seconds")
                pending.remove(h)
                log(f"{h} back up at {st['hosts'][h]['up_at']}")
        if pending:
            time.sleep(POLL_S)
    for h in pending:  # did not return in time
        st["hosts"][h]["status"] = "STUCK_POST"
        incident(h, "stuck_post",
                 f"Reboot was issued ({st['hosts'][h]['reboot']}) but {h} did not come back "
                 f"within {BOOT_TIMEOUT_S}s. Likely hung boot / failed service start.")
    st["phase"] = "models_verify"
    save_state(st)

    # --- wait for models to load on returned remotes (boot tasks do the loading)
    mdeadline = time.monotonic() + MODEL_WAIT_S
    mpending = [h for h in ("Red", "Pale", "Black") if st["hosts"][h]["up_at"]]
    while mpending and time.monotonic() < mdeadline:
        for h in list(mpending):
            ip, _ = HOSTS[h]
            if models_loaded(ip):
                st["hosts"][h]["models_at"] = datetime.now().isoformat(timespec="seconds")
                mpending.remove(h)
                log(f"{h} models resident at {st['hosts'][h]['models_at']}")
        if mpending:
            time.sleep(POLL_S)
    for h in mpending:  # up but no models
        st["hosts"][h]["status"] = "DEGRADED"
        incident(h, "no_models",
                 f"{h} returned from dream reboot but no model resident after {MODEL_WAIT_S}s. "
                 f"Boot task may have failed - run the host's model-load script via WinRM "
                 f"(pattern: white_load_q8.py) or portal /api/inference/load.")
    save_state(st)

    # --- White self-reboot LAST (remotes already verified; minimal blind time)
    st["phase"] = "white_reboot"
    st["hosts"]["White"]["reboot"] = {"ok": True, "method": "shutdown_r_t45",
                                       "at": datetime.now().isoformat(timespec="seconds")}
    save_state(st)
    log("All remotes verified. Rebooting White (self) - dream finalizes after boot.")
    subprocess.run(["shutdown", "/r", "/t", "45"], capture_output=True, text=True, timeout=10)
    st["phase"] = "awaiting_white_boot"
    save_state(st)
    time.sleep(60)   # let the state file settle before White goes down
    return 0

def finalize():
    """Post-White-boot: re-verify remotes, write report, clear the flag."""
    st = load_state()
    for h in ("Red", "Pale", "Black"):
        hs = st.get("hosts", {}).get(h)
        if hs and hs["status"] not in ("STUCK_PRE", "STUCK_POST", "REBOOT_FAILED"):
            p = probe_host(h)
            hs["post"] = p
            if not p["up"]:
                hs["status"] = "STUCK_POST"
                incident(h, "stuck_post", f"{h} down when White finished dream finalization.")
    st["active"] = False
    st["phase"] = "done"
    st["finished"] = datetime.now().isoformat(timespec="seconds")
    save_state(st)
    stuck = [h for h, hs in st.get("hosts", {}).items() if "STUCK" in hs.get("status", "") or hs.get("status") == "REBOOT_FAILED"]
    degraded = [h for h, hs in st.get("hosts", {}).items() if hs.get("status") == "DEGRADED"]
    report = write_report(st, stuck=stuck, degraded=degraded)
    log(f"DREAM DONE: stuck={stuck or 'none'} degraded={degraded or 'none'} report={report}")

# --------------------------------------------------------------------------
def write_report(st, note=None, stuck=None, degraded=None):
    os.makedirs(REPORTS, exist_ok=True)
    day = st.get("started", datetime.now().isoformat())[:10]
    p = os.path.join(REPORTS, f"{day}.md")
    lines = [f"# Dream sync report {day}", "",
             f"Window: daily {DREAM_HOUR:02d}:{DREAM_MIN:02d} + {WINDOW_MIN} min (mandatory all-node quiesce)",
             f"Started: {st.get('started')}  Finished: {st.get('finished', 'pending')}", ""]
    if note:
        lines += [f">> {note} <<", ""]
    lines.append("| Host | Pre-probe | Reboot | Back up | Models | Status |")
    lines.append("|------|-----------|--------|---------|--------|--------|")
    for h, hs in st.get("hosts", {}).items():
        pre = hs.get("pre", {})
        lines.append(f"| {h} | {'up' if pre.get('up') else 'DOWN'}"
                     f"{' +models' if pre.get('models') else ''} "
                     f"| {(hs.get('reboot') or {}).get('method', '-') if (hs.get('reboot') or {}).get('ok') else 'FAILED/-'} "
                     f"| {hs.get('up_at', '-')} | {hs.get('models_at', hs.get('post', {}).get('checked', '-'))} "
                     f"| {hs.get('status', 'ok')} |")
    lines.append("")
    if stuck:
        lines.append(f"## Stuck nodes (deeper recovery required): {', '.join(stuck)}")
        lines.append("See memory/ops/incidents/dream-*.md and runbooks/host_down_response.md.\n")
    if degraded:
        lines.append(f"## Degraded (up, no models): {', '.join(degraded)}\n")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    try:  # pointer for UI / quick reads
        with open(os.path.join(DREAM_DIR, "latest.json"), "w", encoding="utf-8") as f:
            json.dump({"date": day, "report": p, "stuck": stuck or [], "degraded": degraded or []}, f)
    except Exception:
        pass
    return p

def memory_note(st, stuck, degraded):
    """One-line hot note in MEMORY.md (idempotent per day)."""
    try:
        mp = os.path.join(ROOT, "MEMORY.md")
        s = open(mp, encoding="utf-8").read()
        day = st.get("started", "")[:10]
        if f"Dream {day}" in s:
            return
        ok = "all 4 hosts cycled healthy" if not (stuck or degraded) else \
             f"stuck={stuck or '-'} degraded={degraded or '-'}"
        line = f"- DREAM SYNC {day}: daily 5-min all-node quiesce ran; {ok}. Report: memory/dream/reports/{day}.md."
        s = s.replace("## Hot notes", "## Hot notes\n" + line, 1) if "## Hot notes" in s else s + "\n" + line
        open(mp, "w", encoding="utf-8").write(s)
    except Exception as e:
        log(f"memory_note failed: {e}")

# --------------------------------------------------------------------------
def watch():
    st = load_state()
    now = datetime.now()
    if st.get("active"):
        phase = st.get("phase", "?")
        started = st.get("started", "")
        try:
            age = (now - datetime.fromisoformat(started)).total_seconds()
        except Exception:
            age = 1e9
        if phase == "awaiting_white_boot":
            finalize()                      # we are post-boot; finish the dream
        elif phase in ("done_dry", "done"):
            st["active"] = False; save_state(st)
        elif age > ACTIVE_STALE_S:
            log(f"DREAM ABANDONED: active {int(age//60)}min with phase={phase} - clearing flag (safety)")
            incident("fleet", "dream_stale", f"Dream stuck in phase {phase} for {int(age//60)} min; flag cleared.")
            st["active"] = False; save_state(st)
        return 0                            # fresh & running - another process owns it
    if st.get("last_date") == now.date().isoformat() and not st.get("dry_run_pending"):
        return 0                            # today's dream already done
    if in_window(now) or force_requested():
        return run_sequence(dry=dry_requested())
    return 0

def force_requested():
    return "--force" in sys.argv
def dry_requested():
    return "--dry-run" in sys.argv

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    if cmd == "watch":
        return watch()
    if cmd == "run":
        if st := load_state():
            if st.get("active"):
                log("A dream is already active - refusing to start another."); return 1
        return run_sequence(dry=dry_requested(), force=force_requested())
    print(__doc__)
    return 0

if __name__ == "__main__":
    sys.exit(main())
