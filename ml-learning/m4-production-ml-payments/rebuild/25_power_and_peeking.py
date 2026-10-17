"""Rebuild 25: users per arm for a two-proportion test, and the A/A false-positive rate under daily peeking.

Write the two bodies from memory, then run: python rebuild/25_power_and_peeking.py
check() compares them with statsmodels, never with this lab's results.
"""
import math
from statistics import NormalDist

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest


def n_per_arm(p1, rel_lift, alpha=0.05, power=0.80):
    """Users per arm for a two-sided pooled two-proportion z-test to detect p1 moving to p1 * (1 + rel_lift)
    (a drop has a negative rel_lift). Use statistics.NormalDist for the z values and round up to a whole user."""
    raise NotImplementedError("write this from memory")


def aa_false_positive_rates(p, users_per_day, days, n_sims, seed=0, alpha=0.05):
    """n_sims A/A tests: both arms convert at rate p and each gets users_per_day users a day. Draw every count
    at once with np.random.default_rng(seed).binomial(users_per_day, p, size=(n_sims, days, 2)), then run a
    pooled two-proportion z-test on the cumulative counts after every day. Returns (fixed, peeking): the share
    of runs with p below alpha at the last look, and the share with p below alpha at any look."""
    raise NotImplementedError("write this from memory")


def check():
    for p1, lift, alpha, power in [(0.01, 0.10, 0.05, 0.80), (0.05, -0.08, 0.05, 0.90), (0.30, 0.05, 0.01, 0.80),
                                   (0.50, -0.03, 0.10, 0.80), (0.003, 0.15, 0.05, 0.80), (0.90, -0.01, 0.05, 0.90)]:
        ours = n_per_arm(p1, lift, alpha, power)
        h = abs(proportion_effectsize(p1 * (1 + lift), p1))
        ref = NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=power, ratio=1.0)
        assert float(ours).is_integer(), "n_per_arm rounds up to a whole user"
        assert abs(ours / ref - 1) < 0.005, f"n_per_arm{(p1, lift, alpha, power)} = {ours}, statsmodels {ref:.0f}"
    # The A/A simulation against statsmodels' z-test on the same draws, look by look.
    p, users_per_day, days, n_sims, seed = 0.10, 500, 10, 200, 7
    fixed, peeking = aa_false_positive_rates(p, users_per_day, days, n_sims, seed)
    x = np.random.default_rng(seed).binomial(users_per_day, p, size=(n_sims, days, 2)).cumsum(axis=1)
    n = users_per_day * np.arange(1, days + 1)
    sig = np.array([[proportions_ztest(x[i, d], [n[d], n[d]])[1] < 0.05 for d in range(days)] for i in range(n_sims)])
    assert abs(fixed - sig[:, -1].mean()) < 1e-12, "the fixed-horizon rate differs from proportions_ztest"
    assert abs(peeking - sig.any(axis=1).mean()) < 1e-12, "the peeking rate differs from proportions_ztest"
    print("check: PASS")


if __name__ == "__main__":
    check()
