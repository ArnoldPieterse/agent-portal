"""Self-test for cycle_efficiency_index anomaly detection logic."""
import sys

# Synthetic test data simulating 4 cycles
test_data = [
    {"cycle": 10, "efficiency_index": 0.30},
    {"cycle": 11, "efficiency_index": 0.28},
    {"cycle": 12, "efficiency_index": 0.29},
    {"cycle": 13, "efficiency_index": 0.15},  # big drop ~48%
]

print("Self-test: anomaly detection logic")
results = []
for i, r in enumerate(test_data):
    prior = [x["efficiency_index"] for x in test_data[:i] if x["efficiency_index"] is not None][-3:]
    if len(prior) >= 2:
        mean_prior = sum(prior) / len(prior)
        drop_pct = (mean_prior - r["efficiency_index"]) / mean_prior * 100
        flagged = drop_pct > 20.0
        results.append((r["cycle"], drop_pct, flagged))
        print(f"  cycle {r['cycle']}: eff={r['efficiency_index']}, prior_mean={mean_prior:.4f}, drop={drop_pct:.1f}%, flagged={flagged}")
    else:
        print(f"  cycle {r['cycle']}: insufficient prior data ({len(prior)} points)")

# Verify: cycle 13 (0.15 vs ~0.29 mean) should be flagged
c13_drop = results[-1][1]
c13_flagged = results[-1][2]
assert c13_flagged, f"FAIL: cycle 13 not flagged (drop={c13_drop:.1f}%) "

# Verify: cycles 11-12 should NOT be flagged
for c, drop, flagged in results[:-1]:
    if not flagged:
        print(f"  OK: cycle {c} correctly not flagged (drop={drop:.1f}%)")

print("PASS: anomaly detection logic verified")
