# Goal #6 Progress: Loading Skeleton Screens (2026-11-19)

## What was done
- CSS shimmer system added to ui/app.css: @keyframes shimmer (1.4s infinite), .skel base class with ::after gradient overlay, shape-specific classes (.skel-frow, .skel-gtile, .skel-opsbox)
- UI.skeleton(el, shape, count) IIFE added to ui/core.js (inside existing UI namespace bootstrap)
- Hooked into fleetUpdate(): shows 4 skeleton rows before /api/fleet fetch
- Hooked into opsLoad(): shows 1 skeleton box before /api/git fetch

## Verification
- Brace balance: core.js 270/270, app.css 285/285
- Shapes match existing panel layouts (.frow-h, .gtile, .opsbox)

## Remaining for acceptance
- Goals panel hook (no render function found in core.js yet - needs investigation)
- Uploads panel skeleton (ui/uploads.js)
- Live CDP screenshot showing shimmer animation + no layout shift on load
