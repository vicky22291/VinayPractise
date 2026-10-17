"""25. A/B power, peeking and label maturity. Units per arm and calendar days for a fraud-model experiment,
then the false-positive rate of A/A tests that someone checks every day.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Synthetic data only: closed-form sample sizes plus a seeded numpy simulation, so --download fetches nothing.
"""
import math
import sys
from pathlib import Path
from statistics import NormalDist

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import numpy as np
from scipy.stats import chisquare, norm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest

ALPHA, POWER = 0.05, 0.80                  # two-sided test, 80% power
BASE_RATE, BASE_LIFT = 0.02, 0.05          # baseline: a 2% outcome known at once, a 5% relative lift, per user
FRAUD_RATE, FRAUD_LIFT = 0.001, -0.10      # change: fraud at 0.1%, a 10% relative drop, one payment per unit
MATURITY_DAYS = 120                        # change: a fraud label is final 120 days after the payment
PER_ARM_PER_DAY = 1_500_000                # change: payments per arm per day
APPROVAL_FROM, APPROVAL_TO = 0.95, 0.945   # change: the approval-rate guardrail, known at decision time
LOOKS, AA_RUNS = 20, 400                   # break: one look a day for 20 days, 400 A/A runs
SRM_SHARE, SRM_ALPHA = 0.505, 0.001        # baseline: a 50.5/49.5 split, flagged when chi-square p < 0.001


def n_per_arm(p1, rel_lift, alpha=ALPHA, power=POWER):
    """Independent units per arm for a two-sided pooled two-proportion z-test to detect p1 -> p1 * (1 + rel_lift)."""
    p2 = p1 * (1 + rel_lift)
    z_a, z_b = NormalDist().inv_cdf(1 - alpha / 2), NormalDist().inv_cdf(power)
    p_bar = (p1 + p2) / 2
    root = z_a * math.sqrt(2 * p_bar * (1 - p_bar)) + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return math.ceil(root ** 2 / (p2 - p1) ** 2)


def n_per_arm_cohens_h(p1, rel_lift, alpha=ALPHA, power=POWER):
    """The same question asked of statsmodels: Cohen's h (an arcsine distance) with a normal power curve."""
    h = abs(proportion_effectsize(p1 * (1 + rel_lift), p1))
    return math.ceil(NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=power, ratio=1.0))


def aa_false_positive_rates(p, users_per_day, days, n_sims, seed, alpha=ALPHA):
    """n_sims A/A tests: both arms convert at rate p and get users_per_day users a day, and a pooled
    two-proportion z-test runs on the cumulative counts after every day. Returns (fixed, peeking): the share
    of runs with p below alpha at the last look, and the share with p below alpha at any look."""
    rng = np.random.default_rng(seed)
    x = rng.binomial(users_per_day, p, size=(n_sims, days, 2)).cumsum(axis=1)  # conversions so far, per arm
    n = users_per_day * np.arange(1, days + 1)                                  # users so far, per arm
    pooled = x.sum(axis=2) / (2 * n)
    z = (x[:, :, 1] - x[:, :, 0]) / n / np.sqrt(pooled * (1 - pooled) * 2 / n)
    significant = 2 * norm.sf(np.abs(z)) < alpha                                # one p-value per run and look
    return significant[:, -1].mean(), significant.any(axis=1).mean()


def stopped_share_by_look(p, users_per_day, days, n_sims, seed, alpha=ALPHA):
    """For the plot: the same draws, tested with statsmodels' proportions_ztest at every look, then per look
    the share of runs already stopped (p below alpha at that look or an earlier one)."""
    x = np.random.default_rng(seed).binomial(users_per_day, p, size=(n_sims, days, 2)).cumsum(axis=1)
    n = users_per_day * np.arange(1, days + 1)
    p_values = np.array([[proportions_ztest(x[i, d], [n[d], n[d]])[1] for d in range(days)] for i in range(n_sims)])
    return np.logical_or.accumulate(p_values < alpha, axis=1).mean(axis=0)


def plot_peeking(stopped_by, fixed, n_sims, seed):
    """Share of the A/A runs already stopped as significant after each daily look, and the fixed horizon."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    looks = np.arange(1, len(stopped_by) + 1)
    fig, ax = plt.subplots(figsize=(6.4, 3.6), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.plot(looks, stopped_by, color="#2a78d6", lw=2, marker="o", ms=4, label="daily peeking: stopped by this look")
    ax.plot(looks[-1], fixed, "D", color="#eb6834", ms=7, label="fixed horizon: one test after the last day")
    ax.axhline(ALPHA, color="#898781", lw=1, ls="--", label=f"alpha {ALPHA}")
    ax.set(xlabel="daily look", ylabel="false-positive rate", xticks=looks, ylim=(0, None),
           title=f"{n_sims} A/A runs, both arms at {BASE_RATE:.0%}, seed {seed}")
    ax.grid(axis="y", color="#e1e0d9", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    out = labkit.DATA / "results" / "lab25" / f"peeking-seed{seed}{'-smoke' if labkit.smoke() else ''}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PLOT {out}", flush=True)


def baseline(seed):
    n = n_per_arm(BASE_RATE, BASE_LIFT)
    labkit.result("P1.n_per_arm", n, unit="users")
    labkit.result("baseline.n_per_arm_cohens_h", n_per_arm_cohens_h(BASE_RATE, BASE_LIFT), unit="users")
    # Sample-ratio mismatch (SRM) check: assign 2n users with a 50.5% treatment share, test against 50/50.
    treated = int(np.random.default_rng(seed).binomial(2 * n, SRM_SHARE))
    p_value = chisquare([treated, 2 * n - treated]).pvalue
    labkit.result("baseline.srm_p_value", p_value, unit="p")
    labkit.result("baseline.srm_caught", bool(p_value < SRM_ALPHA))


def change(seed):
    n = n_per_arm(FRAUD_RATE, FRAUD_LIFT)
    enrollment_days = math.ceil(n / PER_ARM_PER_DAY)
    labkit.result("change.n_per_arm", n, unit="payments")
    labkit.result("change.n_per_arm_cohens_h", n_per_arm_cohens_h(FRAUD_RATE, FRAUD_LIFT), unit="payments")
    labkit.result("change.enrollment_days", enrollment_days, unit="days")
    labkit.result("P2.calendar_days", enrollment_days + MATURITY_DAYS, unit="days")
    guard_lift = APPROVAL_TO / APPROVAL_FROM - 1  # approval is known at decision time: no maturity wait
    n_guard = n_per_arm(APPROVAL_FROM, guard_lift)
    labkit.result("change.guardrail_n_per_arm", n_guard, unit="payments")
    labkit.result("change.guardrail_n_per_arm_cohens_h", n_per_arm_cohens_h(APPROVAL_FROM, guard_lift), unit="payments")
    labkit.result("change.guardrail_days", n_guard / PER_ARM_PER_DAY, unit="days")  # full traffic, not rounded


def break_(seed, days=LOOKS, n_sims=AA_RUNS):
    users_per_day = math.ceil(n_per_arm(BASE_RATE, BASE_LIFT) / LOOKS)  # the P1 sample, spread over 20 days
    fixed, peeking = aa_false_positive_rates(BASE_RATE, users_per_day, days, n_sims, seed)
    labkit.result("break.fpr_fixed", fixed, unit="fraction")
    labkit.result("P3.fpr_peeking", peeking, unit="fraction")
    plot_peeking(stopped_share_by_look(BASE_RATE, users_per_day, days, n_sims, seed), fixed, n_sims, seed)


args = labkit.start(lab=25, device="cpu")
if args.mode == "download":
    print("NONE lab 25 draws its synthetic data at run time: nothing to fetch", flush=True)
elif args.mode == "smoke":  # every mode's code path, with 5 looks and 20 A/A runs
    baseline(args.seed)
    change(args.seed)
    break_(args.seed, days=5, n_sims=20)
else:
    {"baseline": baseline, "change": change, "break": break_}[args.mode](args.seed)
