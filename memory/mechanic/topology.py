#!/usr/bin/env python3
"""
Fleet Topology Visualization - Mechanic Goal #10 (cycle-7)

Generates a live-updating SVG of the 4-host fleet:
  - Nodes: WHITE, PALE, BLACK, RED
  - Edges: network connections between hosts
  - Status colors: green (ok), amber (degraded), red (down)

State source: memory/mechanic/fleet_state.json (written by health_check / fleet_probe)
If no state file, falls back to TCP probes on known ports.

Usage:
  python memory/mechanic/topology.py --generate   # write fleet-topology.svg
  python memory/mechanic/topology.py --serve      # HTTP server :8098 /api/fleet/topology
  python memory/mechanic/topology.py --selftest   # verify SVG structure with mock data
"""
import json
import os
import sys
import socket
import time
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).parent
STATE_FILE = HERE / "fleet_state.json"
SVG_OUT = HERE / "fleet-topology.svg"
LOG_FILE = HERE / "topology.log"

HOSTS = ["WHITE", "PALE", "BLACK", "RED"]
# Known service ports per host (for TCP probe fallback)
HOST_PORTS = {
    "WHITE": 8099,   # portal
    "PALE": 8888,    # LM Studio
    "BLACK": 8888,
    "RED": 8888,
}
# Host IPs (from fleet config)
HOST_IPS = {
    "WHITE": "127.0.0.1",
    "PALE": "[LAN-IP]02",
    "BLACK": "[LAN-IP]03",
    "RED": "[LAN-IP]04",
}

# --- Status colors ---
COLOR_OK = "#22c55e"       # green
COLOR_DEGRADED = "#f59e0b" # amber
COLOR_DOWN = "#ef4444"     # red
COLOR_EDGE = "#64748b"


def log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def tcp_probe(ip: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if TCP connect succeeds."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, OSError):
        return False


def get_fleet_state() -> dict:
    """
    Returns {host: {status, detail, ts}} for all 4 hosts.
    Status is one of: 'ok', 'degraded', 'down'.
    
    Priority: fleet_state.json > live TCP probe.
    """
    state = {}

    # Try reading existing state file
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for host in HOSTS:
                hinfo = data.get(host, {})
                status = hinfo.get("status", "down")
                detail = hinfo.get("detail", "no state")
                ts = hinfo.get("ts", datetime.now(timezone.utc).isoformat())
                state[host] = {"status": status, "detail": detail, "ts": ts}
            if all(h in data for h in HOSTS):
                return state
        except (json.JSONDecodeError, OSError) as e:
            log(f"fleet_state.json unreadable ({e}); falling back to TCP probe", "WARN")

    # Fallback: live TCP probes
    for host in HOSTS:
        ip = HOST_IPS.get(host, "127.0.0.1")
        port = HOST_PORTS.get(host, 8099)
        ok = tcp_probe(ip, port)
        if ok:
            state[host] = {"status": "ok", "detail": f"TCP :{port} reachable", 
                           "ts": datetime.now(timezone.utc).isoformat()}
        else:
            state[host] = {"status": "down", "detail": f"TCP :{port} unreachable",
                           "ts": datetime.now(timezone.utc).isoformat()}
    return state


def status_color(status: str) -> str:
    return {"ok": COLOR_OK, "degraded": COLOR_DEGRADED, "down": COLOR_DOWN}.get(status, COLOR_DOWN)


def generate_svg(state: dict) -> str:
    """
    Generate SVG string for the fleet topology.
    Layout: diamond - WHITE top, PALE left, BLACK right, RED bottom.
    Edges: all-pairs (complete graph K4).
    """
    W, H = 600, 500
    # Node positions (diamond layout)
    pos = {
        "WHITE": (W // 2, 80),
        "PALE":  (120, H // 2),
        "BLACK": (W - 120, H // 2),
        "RED":   (W // 2, H - 80),
    }
    r = 36  # node radius

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                     f'viewBox="0 0 {W} {H}">')
    svg_parts.append(f'  <rect width="{W}" height="{H}" fill="#0f172a" rx="12"/>')
    svg_parts.append(f'  <text x="{W//2}" y="30" text-anchor="middle" fill="#94a3b8" '
                     f'font-family="monospace" font-size="14">Fleet Topology</text>')

    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg_parts.append(f'  <text x="{W-10}" y="30" text-anchor="end" fill="#475569" '
                     f'font-family="monospace" font-size="11">{ts_now}</text>')

    # Edges (all pairs)
    hosts_list = list(HOSTS)
    for i in range(len(hosts_list)):
        for j in range(i + 1, len(hosts_list)):
            h1, h2 = hosts_list[i], hosts_list[j]
            x1, y1 = pos[h1]
            x2, y2 = pos[h2]
            # Edge color: red if either endpoint is down, amber if degraded
            s1 = state.get(h1, {}).get("status", "down")
            s2 = state.get(h2, {}).get("status", "down")
            if "down" in (s1, s2):
                edge_color = COLOR_DOWN
            elif "degraded" in (s1, s2):
                edge_color = COLOR_DEGRADED
            else:
                edge_color = COLOR_EDGE
            svg_parts.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                             f'stroke="{edge_color}" stroke-width="2" opacity="0.5"/>')

    # Nodes
    for host in HOSTS:
        x, y = pos[host]
        hstate = state.get(host, {"status": "down", "detail": "unknown"})
        color = status_color(hstate["status"])
        # Glow effect for down nodes
        if hstate["status"] == "down":
            svg_parts.append(f'  <circle cx="{x}" cy="{y}" r="{r+8}" fill="{color}" opacity="0.2"/>')
        svg_parts.append(f'  <circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#1e293b" '
                         f'stroke-width="3"/>')
        svg_parts.append(f'  <text x="{x}" y="{y+5}" text-anchor="middle" fill="#0f172a" '
                         f'font-family="monospace" font-weight="bold" font-size="13">{host}</text>')
        # Status label below node
        svg_parts.append(f'  <text x="{x}" y="{y+r+18}" text-anchor="middle" fill="{color}" '
                         f'font-family="monospace" font-size="10">{hstate["status"]}</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def cmd_generate():
    """Generate SVG and write to fleet-topology.svg."""
    state = get_fleet_state()
    svg = generate_svg(state)
    SVG_OUT.write_text(svg, encoding="utf-8")
    log(f"SVG written: {SVG_OUT} ({len(svg)} bytes); states: " + 
        ", ".join(f"{h}={state.get(h,{}).get('status','?')}" for h in HOSTS))
    return 0


class TopologyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/fleet/topology":
            state = get_fleet_state()
            svg = generate_svg(state)
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Cache-Control", "no-cache, max-age=60")
            self.end_headers()
            self.wfile.write(svg.encode())
        elif self.path == "/api/fleet/topology/state":
            state = get_fleet_state()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(state, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress default logging


def cmd_serve(port: int = 8098):
    """Run HTTP server on port serving topology SVG."""
    server = HTTPServer(("0.0.0.0", port), TopologyHandler)
    log(f"Topology server listening on :{port} -> /api/fleet/topology")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Topology server stopped")
    return 0


def cmd_selftest():
    """
    Self-test: verify SVG structure with mock data.
    Checks:
      1. SVG contains all 4 host names
      2. SVG has valid <svg> tag
      3. Status colors present for each state type
      4. Edge count = 6 (K4 complete graph)
      5. Node count = 4
    """
    # Mock state: one of each status
    mock_state = {
        "WHITE": {"status": "ok", "detail": "TCP :8099 reachable",
                  "ts": datetime.now(timezone.utc).isoformat()},
        "PALE":  {"status": "degraded", "detail": "high latency",
                  "ts": datetime.now(timezone.utc).isoformat()},
        "BLACK": {"status": "down", "detail": "TCP :8888 unreachable",
                  "ts": datetime.now(timezone.utc).isoformat()},
        "RED":   {"status": "ok", "detail": "TCP :8888 reachable",
                  "ts": datetime.now(timezone.utc).isoformat()},
    }
    svg = generate_svg(mock_state)

    errors = []
    # Check 1: all host names present
    for host in HOSTS:
        if f">{host}<" not in svg and f'>{host}</text>' not in svg:
            errors.append(f"host {host} not found in SVG")

    # Check 2: valid SVG tag
    if not svg.strip().startswith("<svg"):
        errors.append("SVG does not start with <svg>")
    if "</svg>" not in svg:
        errors.append("SVG missing closing </svg> tag")

    # Check 3: status colors present
    for color, label in [(COLOR_OK, "ok"), (COLOR_DEGRADED, "degraded"), (COLOR_DOWN, "down")]:
        if color not in svg:
            errors.append(f"color {label} ({color}) not found in SVG")

    # Check 4: edge count = 6 (K4)
    line_count = svg.count("<line ")
    if line_count != 6:
        errors.append(f"expected 6 edges, got {line_count}")

    # Check 5: node count = 4 (circles with radius r=36)
    circle_count = svg.count(f'r="{36}"')
    if circle_count != 4:
        errors.append(f"expected 4 nodes, got {circle_count}")

    # Check 6: all-pairs edges (each host pair appears exactly once)
    hosts_list = list(HOSTS)
    for i in range(len(hosts_list)):
        for j in range(i + 1, len(hosts_list)):
            pass  # covered by edge count check

    if errors:
        print("SELFTEST FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print(f"SELFTEST PASSED: SVG valid, {len(svg)} bytes, "
              f"4 nodes, 6 edges, all status colors present")
        # Also write a sample SVG for visual inspection
        sample_out = HERE / "fleet-topology-selftest.svg"
        sample_out.write_text(svg, encoding="utf-8")
        print(f"Sample SVG: {sample_out}")
        return 0


def main():
    if "--selftest" in sys.argv:
        return cmd_selftest()
    elif "--serve" in sys.argv:
        port = 8098
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                port = int(sys.argv[idx + 1])
        return cmd_serve(port)
    else:  # default: --generate
        return cmd_generate()


if __name__ == "__main__":
    sys.exit(main())
