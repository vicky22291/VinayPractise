"""24. Shadow challenger: matched decline rates, swap sets and the latency bill.
Lab 22's champion and challenger replay its 56,962 test payments: decisions at one threshold and at one
decline rate, then the champion's latency alone, with an inline shadow and with a background-thread shadow.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import gc
import math
import queue
import sys
import threading
import time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy: it sets cache defaults
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]  # lab 22's 29 columns, in its order
PARQUET = "https://data.openml.org/datasets/0000/1597/dataset_1597.pq"
LAB22 = labkit.DATA / "models" / "lab22"  # written by lab 22's --baseline at seed 0
BIG = labkit.DATA / "models" / "lab24" / "challenger_lgbm_1000.joblib"  # written by this lab's --download
DECLINE_RATE = 0.002  # the champion's threshold declines this share of the replayed payments
SLOTS, WARMUP, BLOCKS = 50, 100, 5  # thread-shadow queue size; untimed calls per pass; replay blocks
COST_CALLS, PEAK_QPS = 2000, 2000  # single-row calls per CPU-time repeat; decisions a second to size for


def download():
    """Fetch OpenML 1597 (or its parquet copy), check lab 22's files, train the 1,000-tree LightGBM once."""
    try:
        labkit.openml(1597)
        for f in sorted((labkit.DATA / "openml").rglob("creditcard*")):
            print(f"HAVE {f} {f.stat().st_size / 1e6:.1f} MB", flush=True)
    except Exception as e:
        print(f"RETRY parquet fallback ({type(e).__name__})", flush=True)
        labkit.fetch(PARQUET, labkit.DATA / "creditcard" / "dataset_1597.pq", size=73_231_184)
    _, challenger, test_idx = load_models()
    with labkit.locked(BIG):
        if not BIG.exists():
            X, y = load_data()
            train = np.setdiff1d(np.arange(len(y)), test_idx)  # lab 22's training rows
            # learning rate 0.01, not 0.1: at 0.1 the boosting runs out of valid splits long before 1,000 trees
            big = LGBMClassifier(**{**challenger.get_params(), "n_estimators": 1000, "learning_rate": 0.01,
                                    "n_jobs": None})
            joblib.dump(big.fit(X[train], y[train]), BIG)
    print(f"HAVE {BIG} {BIG.stat().st_size / 1e6:.1f} MB, {joblib.load(BIG).booster_.num_trees()} trees", flush=True)


def load_models():
    """Lab 22's champion, challenger and test-row positions; exits 2 with lab 22's command if one is missing."""
    paths = [LAB22 / name for name in ("champion_lr.joblib", "challenger_lgbm.joblib", "test_idx.npy")]
    if not all(p.exists() for p in paths):
        print("MISSING lab 22's models: run python scripts/22_calibration_and_thresholds.py --baseline (seed 0)",
              flush=True)
        sys.exit(2)
    return joblib.load(paths[0]), joblib.load(paths[1]), np.load(paths[2])


def load_data():
    """(X, y): lab 22's FEATURES columns and the 0/1 fraud label, rows in lab 22's order."""
    pq = labkit.DATA / "creditcard" / "dataset_1597.pq"  # there only when a --download needed the fallback
    df = pd.read_parquet(pq) if pq.exists() else labkit.openml(1597)
    y = pd.to_numeric(df["Class"].astype(str)).astype(int).to_numpy()
    return df[FEATURES].to_numpy(dtype=np.float64), y


def matched_threshold(scores, decline_rate):
    """The score above which decline_rate of these scores fall: decline when score > threshold."""
    return float(np.quantile(scores, 1 - decline_rate))


def swap_sets(champ_decl, chal_decl):
    """(overlap, swap_in, swap_out): declined by both, by the challenger only, by the champion only."""
    return (int((champ_decl & chal_decl).sum()), int((chal_decl & ~champ_decl).sum()),
            int((champ_decl & ~chal_decl).sum()))


def python_walk(challenger):
    """The challenger's own trees scored in pure Python: the same probabilities, with the GIL held throughout."""
    def build(node):  # a split becomes (feature, threshold, left, right); a leaf stays its value
        if "leaf_value" in node:
            return node["leaf_value"]
        assert node["decision_type"] == "<=", node["decision_type"]
        return node["split_feature"], node["threshold"], build(node["left_child"]), build(node["right_child"])

    trees = [build(t["tree_structure"]) for t in challenger.booster_.dump_model()["tree_info"]]

    def score(row):
        x, raw = row[0].tolist(), 0.0
        for node in trees:
            while type(node) is tuple:
                feature, threshold, left, right = node
                node = left if x[feature] <= threshold else right
            raw += node
        z = math.exp(-abs(raw))  # a sigmoid that cannot overflow on large raw scores
        return 1.0 / (1.0 + z) if raw >= 0 else z / (1.0 + z)
    return score


class ThreadShadow:
    """A background thread runs score() on queued rows; put() drops a row when the queue is full."""

    def __init__(self, score):
        self.score, self.q, self.sent, self.dropped = score, queue.Queue(SLOTS), 0, 0
        self.worker = threading.Thread(target=self.run, daemon=True)
        self.worker.start()

    def run(self):
        while (row := self.q.get()) is not None:
            self.score(row)  # a real shadow logs this score; nothing acts on it

    def put(self, row):
        self.sent += 1
        try:
            self.q.put_nowait(row)
        except queue.Full:
            self.dropped += 1

    def close(self):
        self.q.put(None)  # waits for a free slot; the worker drains the queue, then stops
        self.worker.join()


def time_requests(rows, handle):
    """handle(row) on the first WARMUP rows untimed, then one timed call per row: latencies in ms."""
    for row in rows[:WARMUP]:
        handle(row)
    gc.collect()  # every pass starts from a collected heap
    ms = []
    for row in rows:
        t0 = time.perf_counter_ns()
        handle(row)
        ms.append((time.perf_counter_ns() - t0) / 1e6)
    return np.array(ms)


def replay(rows, champion, threshold, scorers):
    """Per block: alone, then an inline and a thread shadow per scorer. Latencies per design and block, drop shares."""
    def request(row, shadow=None):  # the champion path: score, decide, then hand the row to the shadow
        decision = champion.predict_proba(row)[0, 1] > threshold
        if shadow is not None:
            shadow(row)
        return decision

    lat, sent, dropped = {"alone": []}, dict.fromkeys(scorers, 0), dict.fromkeys(scorers, 0)
    for block in np.array_split(np.arange(len(rows)), BLOCKS):
        block_rows = [rows[i] for i in block]
        lat["alone"].append(time_requests(block_rows, request))
        for suffix, score in scorers.items():  # inline: scored before the reply; thread: handed off, never waited for
            lat.setdefault(f"inline{suffix}", []).append(time_requests(block_rows, lambda row: request(row, score)))
            shadow = ThreadShadow(score)
            thread_ms = time_requests(block_rows, lambda row: request(row, shadow.put))
            lat.setdefault(f"thread{suffix}", []).append(thread_ms)
            shadow.close()
            sent[suffix], dropped[suffix] = sent[suffix] + shadow.sent, dropped[suffix] + shadow.dropped
    return lat, {suffix: dropped[suffix] / sent[suffix] for suffix in scorers}


def cpu_ms(model, rows):
    """This thread's CPU time per single-row predict_proba in ms: the median of BLOCKS passes over rows."""
    for row in rows[:WARMUP]:
        model.predict_proba(row)
    per_call = []
    for _ in range(BLOCKS):
        t0 = time.thread_time_ns()
        for row in rows:
            model.predict_proba(row)
        per_call.append((time.thread_time_ns() - t0) / 1e6 / len(rows))
    return float(np.median(per_call))


args = labkit.start(lab=24, device="cpu")
if args.mode == "download":
    sys.exit(download())
champion, challenger, test_idx = load_models()
if not BIG.exists():
    print("MISSING the 1,000-tree LightGBM: run python scripts/24_shadow_challenger.py --download", flush=True)
    sys.exit(2)
big = joblib.load(BIG)
for model in (challenger, big):
    model.set_params(n_jobs=1)  # one thread per call: a server scores one payment per request
X, y = load_data()
X, y = X[test_idx], y[test_idx]  # the replay: lab 22's held-out payments, in its order
X, y = (X[:3000], y[:3000]) if labkit.smoke() else (X, y)
p_champ, p_chal = champion.predict_proba(X)[:, 1], challenger.predict_proba(X)[:, 1]  # a row's score ignores other rows
threshold = matched_threshold(p_champ, DECLINE_RATE)  # the champion's threshold
champ_decl = p_champ > threshold
for mode in ("baseline", "change", "break") if labkit.smoke() else (args.mode,):
    if mode == "baseline":
        chal_decl = p_chal > threshold
        labkit.result("P1.challenger_decline_rate", chal_decl.mean(), unit="fraction", n=len(y))
        labkit.result("baseline.champion_threshold", threshold, unit="probability")
        labkit.result("baseline.champion_decline_rate", champ_decl.mean(), unit="fraction", n=len(y))
        labkit.result("baseline.challenger_declines", int(chal_decl.sum()), unit="count")
    elif mode == "change":
        chal_threshold = matched_threshold(p_chal, DECLINE_RATE)
        chal_decl = p_chal > chal_threshold
        overlap, swap_in, swap_out = swap_sets(champ_decl, chal_decl)
        review = lambda mask: float(y[mask].mean()) if mask.any() else float("nan")  # the simulated analyst review
        labkit.result("P2.swap_in_share", swap_in / chal_decl.sum(), unit="fraction")
        labkit.result("change.challenger_threshold", chal_threshold, unit="probability")
        labkit.result("change.challenger_decline_rate", chal_decl.mean(), unit="fraction", n=len(y))
        for name, count in (("overlap", overlap), ("swap_in", swap_in), ("swap_out", swap_out)):
            labkit.result(f"change.{name}", count, unit="count")
        labkit.result("change.swap_in_precision", review(chal_decl & ~champ_decl), unit="fraction")
        labkit.result("change.swap_out_precision", review(champ_decl & ~chal_decl), unit="fraction")
    else:
        order = np.random.default_rng(args.seed).permutation(len(y))  # the seed sets the replay order
        rows = [X[i:i + 1] for i in (order[:600] if labkit.smoke() else order)]  # one 1 x 29 request each
        print(f"DATA payments={len(rows)} blocks={BLOCKS} warmup={WARMUP} slots={SLOTS} "
              f"trees={challenger.n_estimators},{big.booster_.num_trees()}", flush=True)
        walk = python_walk(challenger)
        assert np.allclose([walk(r) for r in rows[:500]], p_chal[order[:500]], rtol=0, atol=1e-12), "walk != LightGBM"
        lat, drops = replay(rows, champion, threshold, {"": challenger.predict_proba, "_walk": walk})
        pct = {d: np.array([np.percentile(ms, (50, 99), method="inverted_cdf") for ms in v]) for d, v in lat.items()}
        p99 = {d: float(np.median(v[:, 1])) for d, v in pct.items()}
        # where each thread design's p99 sits between alone (0) and the same scorer inline (1)
        pos = {s: (p99[f"thread{s}"] - p99["alone"]) / (p99[f"inline{s}"] - p99["alone"]) for s in drops}
        tags = dict(device="cpu", batch=1, warmup=WARMUP, n=len(rows), blocks=BLOCKS)
        labkit.result("P3.closer_to", "inline" if pos[""] > 0.5 else "alone", **tags)
        for s in drops:
            labkit.result(f"break.thread{s}_p99_position", pos[s], unit="ratio")
            labkit.result(f"break.thread{s}_drop_share", drops[s], unit="fraction", slots=SLOTS)
        for d, v in pct.items():
            labkit.result(f"break.p50_{d}_ms", np.median(v[:, 0]), unit="ms", stat="median_of_block_p50", **tags)
            labkit.result(f"break.p99_{d}_ms", p99[d], unit="ms", stat="median_of_block_p99", **tags)
            labkit.result(f"break.p99_block_spread_{d}_ms", np.ptp(v[:, 1]), unit="ms", stat="max_minus_min", **tags)
        cost_rows = rows[:200] if labkit.smoke() else rows[:COST_CALLS]
        for name, model in (("champion", champion), ("lgbm_100", challenger), ("lgbm_1000", big)):
            ms = cpu_ms(model, cost_rows)
            labkit.result(f"break.cpu_ms_{name}", ms, unit="ms", clock="thread_time", batch=1, warmup=WARMUP,
                          n=len(cost_rows), stat="median")
            labkit.result(f"break.cores_{name}", PEAK_QPS * ms / 1000, unit="cores", qps=PEAK_QPS)
