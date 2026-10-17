"""14. An eval set and an LLM judge. Agreement with human verdicts, the human ceiling and position bias.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and pandas: it sets cache defaults
import itertools
import json
import os
import numpy as np
import pandas as pd
import requests

SRC = ("https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/main/data/"
       "human-00000-of-00001-25f4910818759289.parquet")
PARQUET = labkit.DATA / "mt_bench_human_judgments" / "human.parquet"
LAB = labkit.DATA / "lab14"                # the eval set ids, the labelling sheet and your labels
SAVED = labkit.DATA / "results" / "lab14"  # the baseline's verdicts, read by --change and --break
HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434").rstrip("/")
URL = HOST if "://" in HOST else f"http://{HOST}"
MODEL, OPTIONS = "qwen2.5:7b", {"temperature": 0, "seed": 42, "num_ctx": 4096}
N_PAIRS, N_LABEL = 50, 20
JUDGE = ("Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants "
         "to the user question displayed below. You should choose the assistant that follows the user's instructions "
         "and answers the user's question better. Your evaluation should consider factors such as the helpfulness, "
         "relevance, accuracy, depth, creativity, and level of detail of their responses. Avoid any position biases "
         "and ensure that the order in which the responses were presented does not influence your decision. Do not "
         "allow the length of the responses to influence your evaluation. Be as objective as possible.")
FORMAT_V1 = ('Output only a JSON object on one line: {"verdict": "A"} if assistant A is better, '
             '{"verdict": "B"} if assistant B is better.')
FORMAT_V2 = ("Before the verdict, score each answer from 1 (poor) to 3 (good) on correctness, helpfulness and "
             'concision. Output only a JSON object on one line: the scores of assistant A under "a", the scores of '
             'assistant B under "b", then "verdict": "A" if assistant A is better or "B" if assistant B is better.')
PAIR = ("[User Question]\n{question}\n\n[The Start of Assistant A's Answer]\n{a}\n[The End of Assistant A's Answer]"
        "\n\n[The Start of Assistant B's Answer]\n{b}\n[The End of Assistant B's Answer]")


def download():
    labkit.fetch(SRC, PARQUET, size=738_612)


def load_data(seed=0):
    """The eval set: 50 turn-1 pairs with 2 or more human votes and a strict non-tie majority, drawn at the seed.

    A pair is one question and two models, whatever order each human saw them in. Answer A is the model first
    in name order. One row per pair: pair_id, question, answer_a, answer_b, votes (one 'A', 'B' or 'tie' per
    human) and majority ('A' or 'B'). The ids of the draw are saved to ~/ml-data/lab14/eval_ids_seed<S>.csv.
    """
    pairs = {}
    for r in pd.read_parquet(PARQUET).query("turn == 1").itertuples():
        a, b = sorted((r.model_a, r.model_b))
        talk = {r.model_a: r.conversation_a, r.model_b: r.conversation_b}
        pair = pairs.setdefault((r.question_id, a, b), dict(
            question_id=r.question_id, model_a=a, model_b=b, question=talk[a][0]["content"],
            answer_a=talk[a][1]["content"], answer_b=talk[b][1]["content"], votes=[]))
        winner = {"model_a": r.model_a, "model_b": r.model_b}.get(r.winner, "tie")
        pair["votes"].append("tie" if winner == "tie" else "A" if winner == a else "B")
    df = pd.DataFrame(list(pairs.values())).sort_values(["question_id", "model_a", "model_b"])
    counts = pd.DataFrame([{k: v.count(k) for k in ("A", "B", "tie")} for v in df["votes"]], index=df.index)
    unique_top = counts.eq(counts.max(axis=1), axis=0).sum(axis=1) == 1
    df["majority"] = counts.idxmax(axis=1).where(unique_top)
    df = df[(df["votes"].map(len) >= 2) & df["majority"].isin(["A", "B"])].reset_index(drop=True)
    df["pair_id"] = [f"p{i:03d}" for i in range(len(df))]
    draw = df.sample(n=N_PAIRS, random_state=seed).reset_index(drop=True)
    LAB.mkdir(parents=True, exist_ok=True)
    draw[["pair_id", "question_id", "model_a", "model_b"]].to_csv(LAB / f"eval_ids_seed{seed}.csv", index=False)
    return draw


def write_label_sheet():
    """The first 20 pairs at seed 0, for you to label before the session (a human step)."""
    pairs = load_data(0).head(N_LABEL)
    head = ("Lab 14: label these 20 pairs before the session. Read the question and both answers, then write A or B\n"
            "(no ties) next to the pair_id in my_labels.csv: the answer that follows the user's instructions and\n"
            "answers the question better. No lookups, no AI.\n\n")
    blocks = [f"===== {p.pair_id} ({i} of {N_LABEL}) =====\n\n[Question]\n{p.question}\n\n[Answer A]\n{p.answer_a}"
              f"\n\n[Answer B]\n{p.answer_b}\n\n" for i, p in enumerate(pairs.itertuples(), 1)]
    (LAB / "to_label.txt").write_text(head + "".join(blocks))
    if not (LAB / "my_labels.csv").exists():  # never overwrite your labels
        pd.DataFrame({"pair_id": pairs["pair_id"], "my_verdict": ""}).to_csv(LAB / "my_labels.csv", index=False)
    print(f"LABEL {LAB / 'to_label.txt'} and {LAB / 'my_labels.csv'}: {N_LABEL} pairs", flush=True)


def check_server():
    """Stop early, with the fix, when Ollama is down or the model is not pulled."""
    try:
        version = requests.get(f"{URL}/api/version", timeout=5).json()["version"]
        names = [m["name"] for m in requests.get(f"{URL}/api/tags", timeout=5).json()["models"]]
    except requests.RequestException:
        raise SystemExit(f"no Ollama at {URL}: start it with  ollama serve")
    if MODEL not in names:
        raise SystemExit(f"{MODEL} is not pulled: run  ollama pull {MODEL}")
    print(f"OLLAMA {URL} version={version} model={MODEL}", flush=True)


def report(mode, scores, usage, warmup=1):
    """Print one mode's RESULT lines: the contract the lab file names. Shares come in as fractions.

    scores: baseline agreement, kappa, picks_a, human_a, human_human, n_vote_pairs, mine (None before you
    label) and n_mine; change agreement, kappa, picks_a, agreement_v1, right_to_wrong, wrong_to_right;
    break flips, picks_a, agreement. usage: one (prompt tokens, output tokens, seconds) per judged pair,
    from Ollama's prompt_eval_count, eval_count and total_duration; warmup: untimed calls before them.
    """
    s, n = scores, len(usage)
    if mode == "baseline":
        labkit.result("P1.agreement_pct", 100 * s["agreement"], unit="pct", n=n)
        labkit.result("baseline.kappa", s["kappa"], unit="kappa", n=n)
        labkit.result("baseline.picks_a_pct", 100 * s["picks_a"], unit="pct", n=n)
        labkit.result("baseline.human_a_pct", 100 * s["human_a"], unit="pct", n=n)
        labkit.result("baseline.human_human_pct", 100 * s["human_human"], unit="pct", n=s["n_vote_pairs"])
        if s["mine"] is None:
            print(f"SKIP baseline.my_agreement_pct: no verdicts in {LAB / 'my_labels.csv'} (a human step)", flush=True)
        else:
            labkit.result("baseline.my_agreement_pct", 100 * s["mine"], unit="pct", n=s["n_mine"])
    elif mode == "change":
        labkit.result("change.agreement_pct", 100 * s["agreement"], unit="pct", n=n)
        labkit.result("change.kappa", s["kappa"], unit="kappa", n=n)
        labkit.result("change.picks_a_pct", 100 * s["picks_a"], unit="pct", n=n)
        labkit.result("P2.agreement_delta_pts", 100 * (s["agreement"] - s["agreement_v1"]), unit="points", n=n)
        labkit.result("change.right_to_wrong", s["right_to_wrong"], unit="pairs")
        labkit.result("change.wrong_to_right", s["wrong_to_right"], unit="pairs")
    else:
        labkit.result("P3.flip_rate_pct", 100 * s["flips"], unit="pct", n=n)
        labkit.result("break.picks_a_pct", 100 * s["picks_a"], unit="pct", n=n)
        labkit.result("break.agreement_pct", 100 * s["agreement"], unit="pct", n=n)
    medians = np.median(np.asarray(usage, dtype=float), axis=0)
    for name, unit, value in zip(("prompt_tokens", "output_tokens", "s_per_item"), ("tokens", "tokens", "s"), medians):
        labkit.result(f"{mode}.{name}", value, unit=unit, device="ollama", batch=1, warmup=warmup, n=n, stat="median")


# --- the learner's piece, the same as rebuild/14_judge_agreement.py ---
def confusion(human, judge):
    """2 x 2 counts: rows are the human verdict (A, B), columns the judge verdict (A, B)."""
    h, j = np.asarray(human), np.asarray(judge)
    return np.array([[np.sum((h == r) & (j == c)) for c in "AB"] for r in "AB"])


def agreement_and_kappa(human, judge):
    """Raw agreement p_o and Cohen's kappa (p_o - p_e) / (1 - p_e), both from the 2 x 2 table."""
    table = confusion(human, judge) / len(human)
    p_o = np.trace(table)
    p_e = table.sum(axis=1) @ table.sum(axis=0)
    return p_o, (p_o - p_e) / (1 - p_e)


def flip_rate(verdicts_ab, verdicts_ba):
    """Share of pairs whose winner changes when the order swaps. verdicts_ba uses the swapped letters, so a
    kept winner shows up as the other letter and a flip as the same letter."""
    return np.mean(np.asarray(verdicts_ab) == np.asarray(verdicts_ba))


# --- the harness ---
VERDICT = {"type": "string", "enum": ["A", "B"]}
CRITERIA = ["correctness", "helpfulness", "concision"]
SCORES = {"type": "object", "properties": {k: {"type": "integer", "enum": [1, 2, 3]} for k in CRITERIA},
          "required": CRITERIA}
SCHEMA = {1: {"type": "object", "properties": {"verdict": VERDICT}, "required": ["verdict"]},
          2: {"type": "object", "properties": {"a": SCORES, "b": SCORES, "verdict": VERDICT},
              "required": ["a", "b", "verdict"]}}


def ask(question, first, second, version):
    """One /api/chat call. Returns the verdict letter and (prompt tokens, output tokens, seconds)."""
    system = f"{JUDGE} {FORMAT_V1 if version == 1 else FORMAT_V2}"
    body = {"model": MODEL, "stream": False, "format": SCHEMA[version], "options": OPTIONS,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": PAIR.format(question=question, a=first, b=second)}]}
    r = requests.post(f"{URL}/api/chat", json=body, timeout=600)
    r.raise_for_status()
    reply = r.json()
    verdict = json.loads(reply["message"]["content"])["verdict"]
    return verdict, (reply["prompt_eval_count"], reply["eval_count"], reply["total_duration"] / 1e9)


def judge_all(pairs, version, swapped=False):
    """One untimed warm-up call, then every pair once, one request at a time. Letters are as shown."""
    ask("Name a primary colour.", "Red.", "Seven.", version)
    calls = [ask(p.question, *((p.answer_b, p.answer_a) if swapped else (p.answer_a, p.answer_b)), version)
             for p in pairs.itertuples()]
    return [v for v, _ in calls], [use for _, use in calls]


def human_human(pairs):
    """Share of agreeing vote pairs within each pair, tie votes left out, and the number of vote pairs."""
    same = [x == y for votes in pairs["votes"] for x, y in itertools.combinations([v for v in votes if v != "tie"], 2)]
    return float(np.mean(same)), len(same)


def my_agreement(pairs):
    """Your A or B verdicts in my_labels.csv against the human majority, on the pairs in this eval set."""
    path = LAB / "my_labels.csv"
    mine = pd.read_csv(path, dtype=str).fillna("") if path.exists() else pd.DataFrame(columns=["pair_id", "my_verdict"])
    mine = mine.assign(my_verdict=mine["my_verdict"].str.strip().str.upper()).merge(pairs, on="pair_id")
    right = (mine["my_verdict"] == mine["majority"])[mine["my_verdict"].isin(["A", "B"])]
    return (float(right.mean()), len(right)) if len(right) else (None, 0)


def run(mode, pairs, v1=None):
    """Judge the pairs for one mode and print its RESULT lines. Returns the verdicts as shown."""
    human = np.array(pairs["majority"])
    verdicts, usage = judge_all(pairs, version=2 if mode == "change" else 1, swapped=mode == "break")
    v = np.array(verdicts)
    if mode == "baseline":
        agreement, kappa = agreement_and_kappa(human, v)
        (hh, n_vote_pairs), (mine, n_mine) = human_human(pairs), my_agreement(pairs)
        scores = dict(agreement=agreement, kappa=kappa, picks_a=np.mean(v == "A"), human_a=np.mean(human == "A"),
                      human_human=hh, n_vote_pairs=n_vote_pairs, mine=mine, n_mine=n_mine)
    elif mode == "change":
        agreement, kappa = agreement_and_kappa(human, v)
        right_v1, right_v2 = np.array(v1) == human, v == human
        scores = dict(agreement=agreement, kappa=kappa, picks_a=np.mean(v == "A"), agreement_v1=right_v1.mean(),
                      right_to_wrong=int(np.sum(right_v1 & ~right_v2)),
                      wrong_to_right=int(np.sum(~right_v1 & right_v2)))
    else:
        winners = np.where(v == "A", "B", "A")  # the swapped letters, back to answer A and answer B
        scores = dict(flips=flip_rate(v1, v), picks_a=np.mean(winners == "A"), agreement=np.mean(winners == human))
    report(mode, scores, usage)
    return verdicts


if __name__ == "__main__":
    args = labkit.start(lab=14, device="cpu")
    if args.mode == "download":
        download()
        write_label_sheet()
    else:
        check_server()
        pairs, saved = load_data(args.seed), SAVED / f"v1_seed{args.seed}.json"
        if args.mode == "smoke":  # 3 pairs through all three modes, verdicts kept in memory
            v1 = run("baseline", pairs.head(3))
            run("change", pairs.head(3), v1)
            run("break", pairs.head(3), v1)
        elif args.mode == "baseline":
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps({"pair_ids": list(pairs["pair_id"]), "verdicts": run("baseline", pairs)}))
        else:
            v1 = json.loads(saved.read_text()) if saved.exists() else {}
            if v1.get("pair_ids") != list(pairs["pair_id"]):
                print(f"no baseline verdicts for seed {args.seed}: run  python scripts/14_llm_judge.py --baseline "
                      f"--seed {args.seed}")
                sys.exit(2)
            run(args.mode, pairs, v1["verdicts"])
