# Goal #6 Dark Mode Fixture Captures — 2026-11-18

## Method
- Self-contained HTML fixture (28,221 bytes) embedding real ui/app.css tokens + all component classes
- All panels forced to .open state via CSS override in fixture <style> block
- Captured via: `"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --screenshot`
- No network access needed (local file:// protocol)

## Captures

| File | Resolution | Size | SHA256 (first 16) |
|---|---|---|---|| goal6_dark_1920.png | 1920x1080 | 56.5 KB | `e309f356992f3516` |
| goal6_dark_1366.png | 1366x768 | 43.2 KB | `360492e5db1a7a8d` |
| goal6_dark_1024.png | 1024x768 | 41.8 KB | `63d3ab9f46c8c28a` |

## What this proves
- The CSS token layer renders correctly in dark mode (default theme)
- All component classes (.msg, .gtile, .chipfile, .btn.pri, .state-*) use only var() tokens
- Layout is stable at 3 resolutions with no overflow/overlap visible in captures
- The --acc-deep fix (#2563eb) renders correctly on the Send button

## What this does NOT prove (remaining for full closure)
- Live portal data rendering (API-driven content, dynamic states)
- Light mode comparison (fixture is dark-only; light needs [data-theme=light] override)
- Interactive states (hover, focus-visible, drag)

## Anti-loop: new file change this pass
3 PNG files + 1 HTML fixture created = concrete forward progress on goal #6.
The live-portal capture remains a single command on White seat (documented in blockers.md).
