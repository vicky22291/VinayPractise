"""Rebuild 24: a threshold matched to a decline rate, and the swap sets between two decline sets.

Write the two bodies from memory, then run: python rebuild/24_swap_sets.py
check() compares them with numpy, never with this lab's results.
"""
import numpy as np


def matched_threshold(scores, decline_rate):
    """The threshold, by quantile of these scores, at which decline_rate of them are declined: a payment is
    declined when its score > the threshold. Returns a float."""
    return float(np.quantile(np.asarray(scores, dtype=float), 1 - decline_rate))


def swap_sets(champ_decl, chal_decl):
    """Two boolean decline masks over the same payments. Returns (overlap, swap_in, swap_out) as ints: declined
    by both, declined by the challenger only, declined by the champion only."""
    champ_decl, chal_decl = np.asarray(champ_decl, dtype=bool), np.asarray(chal_decl, dtype=bool)
    return (int((champ_decl & chal_decl).sum()), int((chal_decl & ~champ_decl).sum()),
            int((champ_decl & ~chal_decl).sum()))


def check():
    rng = np.random.default_rng(24)
    for n, rate in [(1000, 0.002), (56962, 0.002), (5000, 0.01), (20000, 0.05), (777, 0.1), (100000, 0.0005)]:
        scores = rng.beta(0.5, 20, size=n)  # synthetic continuous scores, no ties
        declined = (scores > float(matched_threshold(scores, rate))).mean()
        assert abs(declined - rate) <= 1 / n, f"n={n}, rate={rate}: declines {declined:.6f}, not within 1/n"
    for n, p_champ, p_chal in [(500, 0.05, 0.08), (10000, 0.002, 0.002), (300, 0.5, 0.3), (50, 0.0, 0.1)]:
        champ, chal = rng.random(n) < p_champ, rng.random(n) < p_chal
        c, l = np.flatnonzero(champ), np.flatnonzero(chal)
        want = (len(np.intersect1d(c, l)), len(np.setdiff1d(l, c)), len(np.setdiff1d(c, l)))
        got = tuple(int(x) for x in swap_sets(champ, chal))
        assert got == want, f"swap_sets gives {got}, numpy intersect1d and setdiff1d give {want}"
    print("check: PASS")


if __name__ == "__main__":
    check()
