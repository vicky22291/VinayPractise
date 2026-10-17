"""15. LLM in production. Time to first token under concurrency, what a JSON schema buys, and a paired regression gate.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
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


def ask(system, query, fmt, seed):
    """One streamed /api/chat call: seconds to the first chunk with content, decode speed, reply text."""
    body = {"model": MODEL, "stream": True, "keep_alive": "10m", "options": {**OPTIONS, "seed": seed},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}]}
    if fmt:
        body["format"] = fmt
    t0, ttft, parts, final = time.perf_counter(), None, [], {}
    with requests.post(f"{URL}/api/chat", json=body, stream=True, timeout=300) as r:
        r.raise_for_status()
        for chunk in (json.loads(line) for line in r.iter_lines() if line):
            assert "error" not in chunk, f"Ollama: {chunk.get('error')}"
            text = chunk.get("message", {}).get("content", "")
            if text and ttft is None:
                ttft = time.perf_counter() - t0
            parts.append(text)
            final = chunk if chunk.get("done") else final
    return {"ttft_s": ttft or time.perf_counter() - t0, "text": "".join(parts),
            "tokens_per_s": final["eval_count"] / (final["eval_duration"] / 1e9)}


def run_pass(system, queries, fmt, c, seed, warm):
    """max(3, c) untimed warm-up calls, then every query with c requests in flight (a closed loop)."""
    with ThreadPoolExecutor(max_workers=c) as pool:
        list(pool.map(lambda q: ask(system, q, fmt, seed), warm[:max(3, c)]))
        t0 = time.perf_counter()
        out = list(pool.map(lambda q: ask(system, q, fmt, seed), queries))
        wall = time.perf_counter() - t0
    return {"ttft_s": [o["ttft_s"] for o in out], "tokens_per_s": [o["tokens_per_s"] for o in out],
            "text": [o["text"] for o in out], "wall_s": wall, "n": len(out), "warmup": max(3, c)}


def parse_intent(text, labels):
    """(intent, status): ok, parse (json.loads fails) or unknown (no 'intent' from the 77 labels)."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None, "parse"
    intent = obj.get("intent") if isinstance(obj, dict) else None
    return (intent, "ok") if intent in labels else (None, "unknown")


def paired_flips(y, pred_a, pred_b):
    """(n_ab, n_ba): items right only under a, and items right only under b."""
    n_ab = sum(a == t and b != t for t, a, b in zip(y, pred_a, pred_b))
    n_ba = sum(a != t and b == t for t, a, b in zip(y, pred_a, pred_b))
    return n_ab, n_ba


def exact_sign_test(n_ab, n_ba):
    """Two-sided exact sign test on the discordant items: min(1, 2 P(X <= min(n_ab, n_ba))), X ~ Bin(n, 1/2)."""
    n = n_ab + n_ba
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(n_ab, n_ba) + 1)) / 2 ** n)


if __name__ == "__main__":
    args = labkit.start(lab=15, device="cpu")
    if args.mode == "download":
        labkit.fetch(f"{SRC}/test.csv", DIR / "test.csv", size=239_961)
        labkit.fetch(f"{SRC}/train.csv", DIR / "train.csv", size=839_073)
        sys.exit()
    check_server()
    test, train, labels = load_data()
    v1 = SYSTEM_V1 + "\n".join(labels)
    shots = train.groupby("category").sample(n=1, random_state=args.seed)  # v2 adds one train example per intent
    v2 = v1 + "\n\nOne example per intent:\n" + "\n".join(
        f'{" ".join(t.split())} => {{"intent": "{c}"}}' for t, c in zip(shots["text"], shots["category"]))
    schema = {"type": "object", "properties": {"intent": {"enum": labels}}, "required": ["intent"]}
    sample = test.groupby("category").sample(n=2, random_state=args.seed).sample(frac=1, random_state=args.seed)
    n = 4 if labkit.smoke() else len(sample)  # smoke: 4 queries through the same code path
    queries, gold = list(sample["text"])[:n], list(sample["category"])[:n]
    warm = list(train["text"].sample(n=8, random_state=args.seed))  # warm-up queries, never scored
    exact = lambda pred: float(np.mean([p == y for p, y in zip(pred, gold)]))
    saved = labkit.DATA / "results" / "lab15" / f"v1_predictions_seed{args.seed}.json"
    if args.mode in ("baseline", "smoke"):
        passes = {c: run_pass(v1, queries, schema, c, args.seed, warm) for c in (1, 4)}
        pred_v1, status = zip(*(parse_intent(t, labels) for t in passes[1]["text"]))
        if not labkit.smoke():
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps({"queries": queries, "pred_v1": pred_v1}))
        report("baseline", passes, {"exact_match_v1": exact(pred_v1), "schema_valid_share": status.count("ok") / n})
    if args.mode in ("change", "smoke"):
        if not labkit.smoke():  # v1's replies come from --baseline at the same seed, so v1 is not sent again
            if not saved.exists() or json.loads(saved.read_text())["queries"] != queries:
                print(f"no v1 predictions for these queries: run --baseline --seed {args.seed} first")
                sys.exit(2)
            pred_v1 = json.loads(saved.read_text())["pred_v1"]
        passes = {1: run_pass(v2, queries, schema, 1, args.seed, warm)}
        pred_v2 = [parse_intent(t, labels)[0] for t in passes[1]["text"]]
        n_ab, n_ba = paired_flips(gold, pred_v1, pred_v2)
        report("change", passes, {"exact_match_v1": exact(pred_v1), "exact_match_v2": exact(pred_v2),
                                  "right_to_wrong": n_ab, "wrong_to_right": n_ba,
                                  "sign_test_p": exact_sign_test(n_ab, n_ba)})
    if args.mode in ("break", "smoke"):
        passes = {8: run_pass(v1, queries[:48], None, 8, args.seed, warm)}
        status = [parse_intent(t, labels)[1] for t in passes[8]["text"]]
        control = run_pass(v1, queries[:48], schema, 8, args.seed, warm)  # matched: same queries and c, schema on
        status_on = [parse_intent(t, labels)[1] for t in control["text"]]
        report("break", passes, {"parse_fail_share": status.count("parse") / len(status),
                                 "unknown_intent_share": status.count("unknown") / len(status),
                                 "with_schema_valid_share": status_on.count("ok") / len(status_on)})
