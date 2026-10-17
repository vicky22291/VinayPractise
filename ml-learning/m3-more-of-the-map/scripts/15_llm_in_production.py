"""15. LLM in production. Time to first token under concurrency, what a JSON schema buys, and a paired regression gate.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import os
import numpy as np
import pandas as pd
import requests

SRC = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data"
DIR = labkit.DATA / "banking77"
MODEL = "qwen2.5:7b"
OPTIONS = {"temperature": 0, "num_predict": 48, "num_ctx": 4096}
URL = "http://" + os.environ.get("OLLAMA_HOST", "127.0.0.1:11434").removeprefix("http://")
SYSTEM_V1 = ("You label messages that customers send to a bank's support team. Choose exactly one intent. "
             'Answer in JSON only, as {"intent": "<label>"}, with <label> copied exactly from this list:\n')


def load_data():
    """BANKING77 test and train queries (columns text and category) and the 77 intent labels, sorted."""
    test, train = pd.read_csv(DIR / "test.csv"), pd.read_csv(DIR / "train.csv")
    return test, train, sorted(test["category"].unique())


def check_server():
    """Stop early, with the fix, when Ollama is down or the model is not pulled."""
    try:
        version = requests.get(f"{URL}/api/version", timeout=5).json()["version"]
        names = [m["name"] for m in requests.get(f"{URL}/api/tags", timeout=5).json()["models"]]
    except requests.RequestException:
        raise SystemExit(f"no Ollama at {URL}: start it with  OLLAMA_NUM_PARALLEL=4 ollama serve")
    if MODEL not in names:
        raise SystemExit(f"{MODEL} is not pulled: run  ollama pull {MODEL}")
    print(f"OLLAMA {URL} version={version} model={MODEL}", flush=True)


def report(mode, passes, scores):
    """Print one mode's RESULT lines: the contract in the lab file's Record table.

    passes maps a concurrency c to one timed pass: ttft_s and tokens_per_s (one value per request),
    wall_s, n (requests) and warmup (untimed calls before it). baseline has c = 1 and 4, change 1,
    break 8 (the pass without the schema).
    scores: baseline exact_match_v1, schema_valid_share; change exact_match_v1, exact_match_v2,
    right_to_wrong, wrong_to_right, sign_test_p; break parse_fail_share, unknown_intent_share (the pass
    without the schema) and with_schema_valid_share (the same queries at the same c, with the schema).
    """
    for c, p in passes.items():
        ms = np.asarray(p["ttft_s"]) * 1000
        tags = dict(device="ollama", batch=1, concurrency=c, warmup=p["warmup"], n=p["n"])
        for q in (50, 95):
            labkit.result(f"{mode}.ttft_p{q}_ms_c{c}", np.percentile(ms, q), unit="ms", stat=f"p{q}", **tags)
        labkit.result(f"{mode}.tokens_per_s_c{c}", np.median(p["tokens_per_s"]), unit="tokens_per_s", stat="median", **tags)
        labkit.result(f"{mode}.mac_s_per_1000_c{c}", p["wall_s"] / p["n"] * 1000, unit="s", **tags)
    if mode == "baseline":
        p95 = {c: np.percentile(p["ttft_s"], 95) for c, p in passes.items()}
        labkit.result("P1.ttft_p95_ratio_c4_c1", p95[4] / p95[1], unit="ratio")
        for name in ("exact_match_v1", "schema_valid_share"):
            labkit.result(f"baseline.{name}", scores[name], unit="fraction")
        labkit.result("baseline.ollama_num_parallel", os.environ.get("OLLAMA_NUM_PARALLEL", "unset"))
    elif mode == "change":
        labkit.result("change.exact_match_v2", scores["exact_match_v2"], unit="fraction")
        labkit.result("P2.exact_match_delta_pts", 100 * (scores["exact_match_v2"] - scores["exact_match_v1"]), unit="points")
        for name in ("right_to_wrong", "wrong_to_right"):
            labkit.result(f"P2.{name}", scores[name], unit="queries")
        labkit.result("change.sign_test_p", scores["sign_test_p"], unit="p_two_sided")
    else:
        bad = scores["parse_fail_share"] + scores["unknown_intent_share"]
        labkit.result("P3.invalid_share", bad, unit="fraction")
        for name in ("parse_fail_share", "unknown_intent_share"):
            labkit.result(f"break.{name}", scores[name], unit="fraction")
        labkit.result("break.schema_valid_share", 1 - bad, unit="fraction")
        labkit.result("break.with_schema_valid_share", scores["with_schema_valid_share"], unit="fraction")


# The harness goes here (see the lab file, section 3). The AI writes the streaming client, the
# concurrent passes, the timing and the three modes from your prompt. You write paired_flips()
# and exact_sign_test() from the lab file's formulas.


if __name__ == "__main__":
    args = labkit.start(lab=15, device="cpu")
    if args.mode == "download":
        labkit.fetch(f"{SRC}/test.csv", DIR / "test.csv", size=239_961)
        labkit.fetch(f"{SRC}/train.csv", DIR / "train.csv", size=839_073)
    elif args.mode == "smoke":  # smoke checks the plumbing only: the server, load_data() and report()
        check_server()
        test, train, labels = load_data()
        print(f"DATA test={len(test)} train={len(train)} labels={len(labels)}", flush=True)
        passes = {c: {"ttft_s": [1.0], "tokens_per_s": [1.0], "wall_s": 1.0, "n": 1, "warmup": max(3, c)}
                  for c in (1, 4, 8)}  # placeholders: smoke hides every value
        scores = dict.fromkeys(["exact_match_v1", "exact_match_v2", "schema_valid_share", "right_to_wrong",
                                "wrong_to_right", "sign_test_p", "parse_fail_share", "unknown_intent_share",
                                "with_schema_valid_share"], 0)
        report("baseline", {c: passes[c] for c in (1, 4)}, scores)
        report("change", {1: passes[1]}, scores)
        report("break", {8: passes[8]}, scores)
    else:
        raise NotImplementedError("write the harness: see the lab file")
