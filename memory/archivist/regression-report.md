# Convergence Regression Report
*generated 2026-11-25T04:26:17.259115+00:00 | window=3 cycles*

**VERDICT: FAIL** - failing: RC3

- **RC1**: PASS  `{"cycle": 23, "delta": 2.2, "band": -2.0}`
- **RC2**: PASS  `{"metrics": {"autonomy_score": {"delta": 2.2, "breach": false}, "interventions_per_cycle": {"delta": -1, "breach": false}}, "breaches": []}`
- **RC3**: FAIL  `{"new_classes": ["data gap (NOT a code bug; proven twice, now with hard evidence - do not re-probe).", "forecast/dispatch desync (NOT a code bug in any archivist script)."], "window_start": "2026-11-23", "source": "ok"}`
- **RC4**: PASS  `{"cycle": 23, "rework_score": 92.5, "floor": 90.0}`
- **RC5**: PASS  `{"slope_per_cycle": 0.0, "tolerance": 0.5, "values": [1, 2, 1]}`
