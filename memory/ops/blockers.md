
## 2026-11-17: Elevation wall - MITIGATED (was BLOCKER)
Admin is now default for all agents via elevated helper service (elev.py -> 127.0.0.1:8098, SYSTEM). Only remaining gate: one-time `install_elevated_helper.bat` UAC click per host (pending user). Until then: `python elev.py ver` exits 5 - note once, do NOT loop on it.
