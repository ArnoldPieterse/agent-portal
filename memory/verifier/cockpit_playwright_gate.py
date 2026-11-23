#!/usr/bin/env python3
"""
cockpit_playwright_gate.py - Cockpit UI Playwright Gate (Verifier Cycle-14 Goal #5)

Automated browser test at 3 viewports: panels render, no JS errors, interactive elements clickable.

Viewports tested:
  - 768x1024 (tablet portrait)
  - 1024x768 (tablet landscape / small desktop)
  - 1440x900 (desktop)

Checks per viewport:
  A. Panels render: key cockpit panel elements exist in DOM
  B. No JS errors: page console shows no uncaught exceptions
  C. Interactive elements clickable: buttons/links respond to click without error

Usage:
  python memory/verifier/cockpit_playwright_gate.py --self-test   # mock mode (no browser needed)
  python memory/verifier/cockpit_playwright_gate.py --live        # real Playwright vs http://127.0.0.1:8099

Exit codes:
  0 = all viewports pass all checks
  1 = one or more checks failed
  2 = usage error
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

RESULTS_FILE = "memory/verifier/cockpit_playwright_gate_results.jsonl"

# Viewports to test
VIEWPORTS = [
    {"name": "tablet_portrait", "width": 768, "height": 1024},
    {"name": "tablet_landscape", "width": 1024, "height": 768},
    {"name": "desktop", "width": 1440, "height": 900},
]

# Key panels that must be present in DOM
REQUIRED_PANELS = [
    "fleet-health",      # fleet health panel
    "active-loops",      # active autonomy loops panel
    "goal-progress",     # goal progress bar/panel
    "recent-alerts",     # recent alerts feed
]

# Interactive elements to test clickability
INTERACTIVE_SELECTORS = [
    ("button.seg", "mode toggle buttons"),
    (".toggles button", "toggle buttons"),
    ("a.nav-link", "nav links"),
]


@dataclass
class ViewportResult:
    viewport: str
    width: int
    height: int
    panels_rendered: bool = False
    panels_found: list = field(default_factory=list)
    js_errors: list = field(default_factory=list)
    interactive_ok: bool = False
    interactive_details: list = field(default_factory=list)
    total_ms: float = 0.0
    passed: bool = False

    def to_dict(self):
        return {
            "viewport": self.viewport,
            "width": self.width,
            "height": self.height,
            "panels_rendered": self.panels_rendered,
            "panels_found": self.panels_found,
            "js_errors": self.js_errors,
            "interactive_ok": self.interactive_ok,
            "interactive_details": self.interactive_details,
            "total_ms": round(self.total_ms, 1),
            "passed": self.passed,
        }


def utc_now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Mock page for self-test mode
# ---------------------------------------------------------------------------

class MockPage:
    """Simulates a Playwright page for self-test without a browser."""

    def __init__(self, viewport_name: str, simulate_js_error: bool = False):
        self.viewport_name = viewport_name
        self._js_errors = []
        if simulate_js_error:
            self._js_errors.append("Uncaught TypeError: mock error for test")

    def query_selector_all(self, selector: str) -> list:
        """Return mock elements for selectors."""
        # Simulate panels existing
        matched_panel = None
        for panel in REQUIRED_PANELS:
            if panel in selector:
                matched_panel = panel
                break
        if matched_panel:
            return [MockElement(f"panel-{matched_panel}")]
        # Simulate interactive elements
        for sel, _ in INTERACTIVE_SELECTORS:
            if sel.split()[0] == selector.split()[0]:
                return [MockElement(f"el-{selector}"), MockElement(f"el2-{selector}")]
        return []

    def on(self, event: str, callback):
        """Register event handler (no-op in mock)."""
        pass

    def goto(self, url: str):
        pass

    def wait_for_load_state(self, state="load"):
        pass

    @property
    def console_messages(self) -> list:
        return self._js_errors


class MockElement:
    def __init__(self, name):
        self.name = name
        self.is_visible = True
        self.is_enabled = True

    def click(self, timeout=5000):
        pass  # succeeds in mock


# ---------------------------------------------------------------------------
# Live page wrapper (requires playwright)
# ---------------------------------------------------------------------------

class LivePage:
    """Wraps a real Playwright page."""

    def __init__(self, browser, viewport_name: str, width: int, height: int, url: str):
        self.viewport_name = viewport_name
        context = browser.new_context(viewport={"width": width, "height": height})
        self.page = context.new_page()
        self._js_errors = []
        self.page.on("console", self._on_console)
        self.page.goto(url, wait_until="networkidle", timeout=15000)

    def _on_console(self, msg):
        if msg.type == "error":
            self._js_errors.append(msg.text)

    def query_selector_all(self, selector: str) -> list:
        return self.page.query_selector_all(selector)

    @property
    def console_messages(self) -> list:
        return self._js_errors

    def close(self):
        self.page.context.close()


# ---------------------------------------------------------------------------
# Core test logic (viewport-agnostic)
# ---------------------------------------------------------------------------

def run_viewport_checks(page, viewport_name: str, width: int, height: int) -> ViewportResult:
    """Run all checks for a single viewport. Works with MockPage or LivePage."""
    start = time.monotonic()
    result = ViewportResult(viewport=viewport_name, width=width, height=height)

    # Check A: Panels render
    panels_found = []
    for panel_id in REQUIRED_PANELS:
        selector = f"[data-panel='{panel_id}'], #{panel_id}, .{panel_id}"
        elements = page.query_selector_all(selector)
        if elements:
            panels_found.append(panel_id)
    result.panels_found = panels_found
    result.panels_rendered = len(panels_found) == len(REQUIRED_PANELS)

    # Check B: No JS errors
    result.js_errors = list(page.console_messages)
    no_js_errors = len(result.js_errors) == 0

    # Check C: Interactive elements clickable
    interactive_ok = True
    for selector, desc in INTERACTIVE_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
            if not elements:
                result.interactive_details.append(f"{desc}: NOT FOUND")
                continue
            el = elements[0]
            if hasattr(el, 'is_visible') and not el.is_visible:
                result.interactive_details.append(f"{desc}: not visible")
                interactive_ok = False
                continue
            el.click(timeout=3000)
            result.interactive_details.append(f"{desc}: OK ({len(elements)} found)")
        except Exception as e:
            result.interactive_details.append(f"{desc}: CLICK FAILED ({str(e)[:60]})")
            interactive_ok = False
    result.interactive_ok = interactive_ok

    # Overall pass
    result.passed = result.panels_rendered and no_js_errors and result.interactive_ok
    result.total_ms = (time.monotonic() - start) * 1000
    return result


# ---------------------------------------------------------------------------
# Self-test (mock mode)
# ---------------------------------------------------------------------------

def self_test():
    print("=== Cockpit Playwright Gate: SELF-TEST ===\n")
    all_pass = True

    # Test 1: All viewports pass with good mock
    print("[T1] All 3 viewports - clean state (should PASS)")
    for vp in VIEWPORTS:
        page = MockPage(vp["name"])
        r = run_viewport_checks(page, vp["name"], vp["width"], vp["height"])
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            all_pass = False
        print(f"  {vp['name']} ({vp['width']}x{vp['height']}): {status} "
              f"(panels={len(r.panels_found)}/{len(REQUIRED_PANELS)}, "
              f"js_errors={len(r.js_errors)}, interactive_ok={r.interactive_ok})")

    # Test 2: Simulate JS error -> should FAIL
    print("\n[T2] Simulated JS error (should FAIL)")
    page = MockPage("desktop", simulate_js_error=True)
    r = run_viewport_checks(page, "desktop", 1440, 900)
    t2_pass = not r.passed and len(r.js_errors) > 0
    status = "PASS" if t2_pass else "FAIL"
    if not t2_pass:
        all_pass = False
    print(f"  desktop with JS error: {status} (js_errors={r.js_errors[:1]})")

    # Test 3: Verify result structure is machine-readable JSON
    print("\n[T3] Result structure validation")
    d = r.to_dict()
    required_keys = {"viewport", "width", "height", "panels_rendered",
                     "js_errors", "interactive_ok", "passed"}
    t3_pass = required_keys.issubset(set(d.keys()))
    status = "PASS" if t3_pass else "FAIL"
    if not t3_pass:
        all_pass = False
    print(f"  JSON structure has all required keys: {status}")

    # Test 4: Write results to file
    print("\n[T4] Results file write")
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    entry = {"ts": utc_now(), "mode": "self-test", "viewports": [r.to_dict()]}
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    t4_pass = os.path.exists(RESULTS_FILE)
    status = "PASS" if t4_pass else "FAIL"
    if not t4_pass:
        all_pass = False
    print(f"  Results written to {RESULTS_FILE}: {status}")

    # Summary
    print(f"\n=== SELF-TEST RESULT: {'ALL PASS' if all_pass else 'FAILURES'} ===")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Live mode (requires playwright + running cockpit server)
# ---------------------------------------------------------------------------

def live_test(url: str = "http://127.0.0.1:8099"):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        return 2

    print(f"=== Cockpit Playwright Gate: LIVE MODE ({url}) ===\n")
    all_pass = True
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            try:
                page = LivePage(browser, vp["name"], vp["width"], vp["height"], url)
                r = run_viewport_checks(page, vp["name"], vp["width"], vp["height"])
                results.append(r.to_dict())
                status = "PASS" if r.passed else "FAIL"
                if not r.passed:
                    all_pass = False
                print(f"  {vp['name']} ({vp['width']}x{vp['height']}): {status} "
                      f"(panels={len(r.panels_found)}/{len(REQUIRED_PANELS)}, "
                      f"js_errors={len(r.js_errors)}, interactive_ok={r.interactive_ok})")
                page.close()
            except Exception as e:
                results.append({"viewport": vp["name"], "passed": False, "error": str(e)[:100]})
                all_pass = False
                print(f"  {vp['name']}: ERROR - {str(e)[:80]}")
        browser.close()

    # Write results
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    entry = {"ts": utc_now(), "mode": "live", "url": url, "viewports": results}
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"\n=== LIVE RESULT: {'ALL PASS' if all_pass else 'FAILURES'} ===")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

import os

def main():
    parser = argparse.ArgumentParser(description="Cockpit UI Playwright Gate")
    parser.add_argument("--self-test", action="store_true", help="Run mock self-test (no browser needed)")
    parser.add_argument("--live", action="store_true", help="Run live test with Playwright")
    parser.add_argument("--url", default="http://127.0.0.1:8099", help="Cockpit URL for live mode")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())
    elif args.live:
        sys.exit(live_test(args.url))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
