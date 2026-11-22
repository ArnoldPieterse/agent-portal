# Goal 1 (WinRM) - closure path made functional + RED IP bug fixed [2026-11-20]

Two latent defects in the goal-1 closure path found + fixed this pass (in-sandbox, no wall involved).
Goal 1 is NOT closed - live 4-host exec still needs a non-sandbox seat (see blockers.md Mechanic #1).
But these two bugs would have made that non-sandbox run FAIL for spurious reasons.

## Defect 1: winrm_pool.py had NO CLI entry point
- File ended at a bare `# --- CLI entry point ---` comment with no argv handling (no `__main__`,
  no argparse). So `close_goal1.bat`'s calls `python winrm_pool.py health` and
  `python winrm_pool.py rotation-status` were SILENT NO-OPS -> exit 0 without doing anything.
- Consequence: close_goal1.bat's `if errorlevel 1 (goto :fail)` gate on the health step was a
  FALSE-PASS - it would "succeed" on a non-sandbox run without ever probing the hosts.
- The advertised `--preflight` subcommand was ALSO a no-op (the `preflight()` function existed but
  nothing called it). The hot-note "4/5 pass" was from an earlier revision; current file had no CLI.
- FIX: added `if __name__ == '__main__'` block with 3 subcommands:
    --preflight      -> preflight(); exit 0 iff all checks pass
    health           -> WinRMPool().health_check_all(); exit 0 only if ALL 4 hosts OK (real gate)
    rotation-status  -> per-host check_credential_rotation(); exit 0 (informational, never gates)
- VERIFIED in-sandbox via a throwaway batch (captured true runtime %ERRORLEVEL%, not the `&` parse
  artifact): PREFLIGHT_EXIT=1 (pywinrm missing here - expected), ROTATION_EXIT=0, HEALTH_EXIT=1
  (non-local hosts unreachable from sandbox - EXPECTED, and proves the gate is now REAL: it fails
  here precisely because we cannot reach PALE/BLACK/RED; on a non-sandbox White seat with LAN egress
  + pywinrm it runs live exec and passes only if all 4 OK).
- Regression check: `python memory/mechanic/winrm_pool_selftest.py` still 20/20 PASS, 0 FAIL.

## Defect 2: RED host IP typo ([redacted-LAN-IP] -> Red)
- winrm_pool.py HOSTS['RED'] had ip=[redacted-LAN-IP], but the canonical Red IP is Red
  (confirmed across agents.json, agent_portal.py _FLEET_REBOOT_USERS, boot_recovery.py,
  egress_guard.py, capability_registry.json, hotload-catalog.json, memory_mirror_hosts.json and
  every deploy_*.py). Only 3 mechanic files had the .50 typo.
- Consequence: `close_goal1.bat health` would try to reach the WRONG IP for RED and report it
  UNREACHABLE even from a perfectly good non-sandbox seat -> goal-1 closure blocked for the wrong reason.
- FIX: corrected RED ip to Red in:
    memory/mechanic/winrm_pool.py      (closure path - critical)
    memory/mechanic/winrm_ntlm_full.py (probe script)
    memory/mechanic/_winrm_probe_now.py(probe script)
- VERIFIED: all 3 compile clean; zero remaining '[redacted-LAN-IP]' occurrences in the three files.

## Net effect
- close_goal1.bat is now end-to-end correct: it will perform a REAL 4-host health gate and record
  evidence, not false-pass. Remaining leg = live exec on non-sandbox White seat (pywinrm + LAN egress).
- One-line runbook note: "close_goal1.bat was a silent no-op (winrm_pool.py had no CLI) AND pointed
  at the wrong Red IP (.50); added the CLI (--preflight/health/rotation-status) and fixed RED to .245 -
  the bat now genuinely gates on live host status."
