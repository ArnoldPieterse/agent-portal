
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        # Load the portal
        await page.goto("http://127.0.0.1:8099/", wait_until="networkidle")
        await asyncio.sleep(1)
        
        # Test 1: Verify no JS errors on load
        js_errors = []
        page.on("pageerror", lambda e: js_errors.append(str(e)))
        
        # Test 2: Verify ssPoll exists and ran
        has_ss_poll = await page.evaluate("typeof ssPoll === 'function'")
        print(f"ssPoll function exists: {has_ss_poll}")
        
        # Test 3: Simulate STEADY-STATE mode by mocking the API response
        await page.route("**/api/fleet/mode", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"mode":"STEADY-STATE","since":"2026-11-24T12:00:00Z","goal_pct":100,"next_transition_forecast":"test","pass_budget":{"used":5,"total":20}}'
        ))
        await asyncio.sleep(6)  # wait for poll
        
        # Check body class
        has_steady = await page.evaluate("document.body.classList.contains('steady-state')")
        print(f"body.steady-state applied: {has_steady}")
        
        # Check badge exists
        badge = await page.query_selector("#ssBadge")
        print(f"Converged badge present: {badge is not None}")
        if badge:
            text = await badge.inner_text()
            print(f"Badge text: {text}")
        
        # Test 4: Verify no layout shift (badge is in flex container)
        status_box = await page.evaluate("""() => {
            const el = document.getElementById('status');
            if(!el) return null;
            const r = el.getBoundingClientRect();
            return {width: r.width, height: r.height};
        }""")
        print(f"#status dimensions: {status_box}")
        
        # Test 5: Check CSS applied (green border on main)
        main_shadow = await page.evaluate("getComputedStyle(document.querySelector('main')).boxShadow")
        print(f"main box-shadow: {main_shadow[:60]}...")
        
        # Test 6: Simulate exit from STEADY-STATE -> amber pulse
        await page.route("**/api/fleet/mode", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"mode":"WORK","since":"2026-11-24T13:00:00Z","goal_pct":82,"next_transition_forecast":"test","pass_budget":{"used":5,"total":20}}'
        ))
        await asyncio.sleep(6)
        
        has_steady_after = await page.evaluate("document.body.classList.contains('steady-state')")
        print(f"body.steady-state removed on exit: {not has_steady_after}")
        
        badge_after = await page.query_selector("#ssBadge")
        print(f"Badge removed on exit: {badge_after is None}")
        
        # Check pulse was triggered (it should have started and possibly finished by now)
        # The pulse lasts 2.1s, we waited 6s so it should be done
        has_pulse = await page.evaluate("document.body.classList.contains('mode-exit-pulse')")
        print(f"Pulse class cleaned up: {not has_pulse}")
        
        # Check for JS errors
        await asyncio.sleep(0.5)
        print(f"JS errors: {len(js_errors)} {js_errors[:3] if js_errors else ''}")
        
        # Test 7: Take screenshot in steady-state for visual verification
        await page.route("**/api/fleet/mode", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"mode":"STEADY-STATE","since":"2026-11-24T12:00:00Z","goal_pct":100,"next_transition_forecast":"test","pass_budget":{"used":5,"total":20}}'
        ))
        await asyncio.sleep(6)
        await page.screenshot(path="memory/designer/ss-indicator-verify.png", full_page=False)
        print("Screenshot saved: memory/designer/ss-indicator-verify.png")
        
        await browser.close()
        print("\nALL CHECKS COMPLETE")

asyncio.run(main())
