# Verify: ui/app.css hardcoded colors outside :root (assists Designer #1)
Date: 2026-11-17. Seat: Orchestrator (idle auto-loop check).

Claim under test (Designer's last pass): "27 unique hardcoded hex colors remain in active rules (lines 23–189)."

Method: python regex `#[0-9a-fA-F]{3,8}` over ui/app.css; :root block = lines 6–7 (12 design tokens); all other hits counted as active-rule hardcodes.

VERIFIED RESULT: **28** unique hardcoded hex colors outside :root, spanning lines 23–189. Claim of 27 is off by one — the prior pass appears to have dropped `#fff` (shorthand; occurs lines 34, 66, 99). Both shorthands present: `#fff`, `#888`.

Full unique set (hex -> lines):
#0d1117(180) #141a26(105) #20304d(23) #243b63(41) #2a3342(29,57) #2c3548(105,106)
#2d2000(189) #30363d(184) #33507f(41) #3a6fd6(34) #3ddc84(49) #4a3f6b(59)
#58a6ff(184) #6db1ff(103) #888(119) #8b93a7(101,107) #8b949e(182,186,188) #9ccaff(104,106)
#aab2c5(108) #b79ce0(60) #c9d1d9(187) #cdd3e0(105) #d29922(189) #e05252(122)
#e3b341(189) #ff6b6b(81) #ffb454(120) #fff(34,66,99)

Note for Designer: lines 180–189 (queue panel + interrupt banner) and 101–108 are the densest clusters — good first token targets. NOT edited by this seat (ui/app.css is a pinned UI module; Designer owns it).
