# Power-limit decision 2026-11-26 (user asked: set all cards to 800W)

## Verdict: 800W is NOT safe/settable on stock cards - corrected
- Driver ceiling per card (nvidia-smi -q -d POWER, White): Min 400 / Default 600 / **Max 600 W**. `nvidia-smi -pl 800` is rejected ("Invalid Power Limit Request").
- Web research: the "800W RTX 5090" figure comes from a **shunt-resistor hardware mod** (TweakTown: ASUS ROG Astral 5090 + shunt mod) or unofficial bypass tools (TechPowerUp 2026-08-24: mVolt+ v0.36, 5090 OC hits 700W). Both void warranty; 12VHPWR connector is rated ~600W and 5090 transients are the known melting failure mode (BottleneckPC/SlashGear: measured system peak ~856W at 575W board power). NVIDIA caps driver limit at 600W precisely for this.

## Fleet state + action
- White (local): 2x RTX 5090 already at 600W = max. No change needed.
- Pale (IP_LAN): 2x RTX 5090. GPU1 was capped 450W this morning (heat mitigation, temps were ~89-92C under load). Current probe: [('0', '43.02', '27.37 W'), ('1', '60.90', '429.74 W')]; caps_before: [('27', '600'), ('429', '450')]. Decision: **restore-600**.
- Applied on Pale: n/a

## Follow-ups (open)
1. `-pl` does NOT survive reboot on Windows. Add power-limit restore to the boot chain (T7 hardening) so caps persist after restarts - same mechanism as the watchdog/elev fix.
2. If Pale GPU1 stays hot under load at 600W, re-apply 450W cap and log it in memory/ops/pale-heat.md.

## Compaction rule (user instruction 2026-11-26)
When low context is detected ("no room in the window" / omitted results), FIRST run prep: write current state + verdicts to memory/ops/*.md and TODO.md, then continue. Do not let compaction eat un-persisted decisions.
