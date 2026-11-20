"""
boot_verify.py - Post-reboot model + agent verification (Mechanic goal #6)

After each reboot, verify all model reload boot tasks executed correctly:
  1. Check nvidia-smi for expected GPU models loaded
  2. Probe LM Studio aliases via /api/v0/models
  3. Confirm agents respond (portal health at :8099)
  4. Write verification log to memory/mechanic/boot-verify-YYYY-MM-DD.md

Usage:
  python memory/mechanic/boot_verify.py            # full check, write report
  python memory/mechanic/boot_verify.py --dry-run  # check only, no file write
  python memory/mechanic/boot_verify.py --json     # output JSON (for automation)

Exit codes: 0 = all pass, 1 = some failures, 2 = fatal (no connectivity at all)
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---
LM_STUDIO_URL = "http://127.0.0.1:8888"
PORTAL_URL = "http://127.0.0.1:8099"
EXPECTED_MODELS = [
    "atlas-q8",        # Orchestrator
    "quinn-q4",        # Researcher
    "Qwen3.8-27B-Q8_0",  # Builder + Verifier (shared)
    "designer-q4",     # Designer
    "archivist-q8",    # Archivist
    "scribe-q8",       # Scribe
    "mechanic-q4",     # Mechanic
]
OUTPUT_DIR = Path("memory/mechanic")
TIMEOUT_S = 10


def _http_get(url: str, timeout: int = TIMEOUT_S) -> tuple[int, bytes | None]:
    """Simple HTTP GET returning (status_code, body_bytes)."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else None
    except (urllib.error.URLError, OSError) as e:
        return -1, str(e).encode()


def check_nvidia_smi() -> dict:
    """Check nvidia-smi for loaded models. Returns {models_found: [...], raw: str}."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=process_name,pid,used_memory",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout).strip()[:200]
            return {"models_found": 0, "processes": [], "ok": False, "error": f"nvidia-smi rc={result.returncode}: {err}"}
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()
                 and not l.lower().startswith("failed to initialize")]
        return {"models_found": len(lines), "processes": lines, "ok": True}
    except FileNotFoundError:
        return {"models_found": 0, "processes": [], "ok": False, "error": "nvidia-smi not found"}
    except subprocess.TimeoutExpired:
        return {"models_found": 0, "processes": [], "ok": False, "error": "nvidia-smi timeout"}


def check_lm_studio_models() -> dict:
    """Probe LM Studio /api/v0/models for loaded model aliases."""
    status, body = _http_get(f"{LM_STUDIO_URL}/api/v0/models")
    if status != 200 or body is None:
        return {"loaded": [], "ok": False, "error": f"HTTP {status}"}
    try:
        data = json.loads(body)
        models = [m.get("id", m.get("name", "?")) for m in data.get("data", [])]
        return {"loaded": models, "ok": True}
    except (json.JSONDecodeError, KeyError):
        return {"loaded": [], "ok": False, "error": "bad JSON from LM Studio"}


def check_portal_health() -> dict:
    """Check portal :8099 health endpoint."""
    status, body = _http_get(f"{PORTAL_URL}/api/health")
    if status == 200:
        try:
            data = json.loads(body)
            return {"ok": True, "status": data}
        except json.JSONDecodeError:
            return {"ok": True, "raw": body.decode(errors="replace")[:200]}
    elif status == -1:
        return {"ok": False, "error": f"portal unreachable: {body.decode(errors='replace')[:100]}"}
    else:
        return {"ok": False, "error": f"HTTP {status}"}


def verify() -> dict:
    """Run all checks and return structured results."""
    ts = datetime.now(timezone.utc).isoformat()
    results = {
        "timestamp": ts,
        "checks": {},
        "overall": "PASS",
    }

    # 1. nvidia-smi
    nv = check_nvidia_smi()
    results["checks"]["nvidia_smi"] = nv
    if not nv.get("ok"):
        results["overall"] = "FAIL"

    # 2. LM Studio models
    lm = check_lm_studio_models()
    results["checks"]["lm_studio"] = lm
    if lm.get("ok"):
        loaded_set = set(lm["loaded"])
        missing = [m for m in EXPECTED_MODELS if m not in loaded_set]
        extra = [m for m in loaded_set if m not in EXPECTED_MODELS]
        results["checks"]["lm_studio"]["missing_expected"] = missing
        results["checks"]["lm_studio"]["extra_loaded"] = extra
        if missing:
            results["overall"] = "FAIL"
    else:
        results["overall"] = "FAIL"

    # 3. Portal health
    portal = check_portal_health()
    results["checks"]["portal"] = portal
    if not portal.get("ok"):
        results["overall"] = "FAIL"

    return results


def write_report(results: dict) -> str:
    """Write boot-verify report to memory/mechanic/boot-verify-YYYY-MM-DD.md."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = OUTPUT_DIR / f"boot-verify-{date_str}.md"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Boot Verification Report - {date_str}",
        f"Generated: {results['timestamp']}",
        f"Overall: **{results['overall']}**",
        "",
        "## Checks",
        "",
    ]

    nv = results["checks"].get("nvidia_smi", {})
    lines.append(f"### nvidia-smi: {'PASS' if nv.get('ok') else 'FAIL'}")
    if nv.get("processes"):
        for p in nv["processes"]:
            lines.append(f"  - {p}")
    elif not nv.get("ok"):
        lines.append(f"  Error: {nv.get('error', 'unknown')}")
    lines.append("")

    lm = results["checks"].get("lm_studio", {})
    lines.append(f"### LM Studio Models: {'PASS' if lm.get('ok') else 'FAIL'}")
    if lm.get("ok"):
        lines.append(f"  Loaded ({len(lm['loaded'])}): {', '.join(sorted(lm['loaded']))}")
        if lm.get("missing_expected"):
            lines.append(f"  MISSING: {', '.join(lm['missing_expected'])}")
        if lm.get("extra_loaded"):
            lines.append(f"  Extra (unexpected): {', '.join(lm['extra_loaded'])}")
    else:
        lines.append(f"  Error: {lm.get('error', 'unknown')}")
    lines.append("")

    portal = results["checks"].get("portal", {})
    lines.append(f"### Portal Health: {'PASS' if portal.get('ok') else 'FAIL'}")
    if portal.get("ok"):
        status = portal.get("status", portal.get("raw", "200 OK"))
        lines.append(f"  Status: {status}")
    else:
        lines.append(f"  Error: {portal.get('error', 'unknown')}")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def main():
    dry_run = "--dry-run" in sys.argv
    json_out = "--json" in sys.argv

    results = verify()

    if json_out:
        print(json.dumps(results, indent=2))
    else:
        print(f"Boot Verification - {results['timestamp']}")
        print(f"Overall: {results['overall']}")
        for name, check in results["checks"].items():
            status = "PASS" if check.get("ok") else "FAIL"
            detail = ""
            if name == "lm_studio" and check.get("missing_expected"):
                detail = f" (missing: {', '.join(check['missing_expected'])})"
            print(f"  [{status}] {name}{detail}")

    if not dry_run and results["overall"] in ("PASS", "FAIL"):
        path = write_report(results)
        if not json_out:
            print(f"Report written: {path}")

    sys.exit(0 if results["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
