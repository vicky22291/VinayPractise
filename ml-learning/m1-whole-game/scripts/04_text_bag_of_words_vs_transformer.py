"""04. Text: bag of words vs a pretrained transformer. TF-IDF vs DistilBERT on 2,000 IMDB reviews: accuracy and cost.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import json
import statistics
import sys
import timeit
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import numpy as np
import pandas as pd
import torch
import transformers
from huggingface_hub import snapshot_download
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

HF = "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/main/plain_text/{}-00000-of-00001.parquet"
SIZES = {"train": 20_979_968, "test": 20_470_363}  # the unsupervised split is not needed
DIR, MODEL = labkit.DATA / "imdb", "distilbert/distilbert-base-uncased"
N_TRAIN, N_TEST, TEST_SEED = 2_000, 2_000, 0  # the test subset is the same 2,000 reviews at every --seed
LONG, SHORT = 256, 32                         # word pieces per review: baseline and break, then the change
EPOCHS, BATCH, LR, WARMUP, CPU_BATCH = 2, 16, 5e-5, 0.1, 50  # CPU timing: 20 batches of 50 = 1,000 reviews
transformers.logging.set_verbosity_error()
transformers.logging.disable_progress_bar()


def download():
    try:
        for split, size in SIZES.items():
            labkit.fetch(HF.format(split), DIR / f"{split}.parquet", size=size)
    except OSError:  # fallback (labkit printed why): the fast.ai archive holds the same reviews, one .txt file each
        root = labkit.extract(labkit.fetch("https://s3.amazonaws.com/fast-ai-nlp/imdb.tgz", DIR / "imdb.tgz"), DIR) / "imdb"
        for split in SIZES:
            rows = [(f.read_text(encoding="utf-8"), label) for label, name in enumerate(("neg", "pos"))
                    for f in sorted((root / split / name).glob("*.txt"))]
            pd.DataFrame(rows, columns=["text", "label"]).to_parquet(DIR / f"{split}.parquet")
    with labkit.locked(labkit.DATA / "hf" / MODEL.replace("/", "--")):
        path = Path(snapshot_download(MODEL, allow_patterns=["*.json", "vocab.txt", "model.safetensors"]))
    print(f"HAVE {path} {sum(f.stat().st_size for f in path.iterdir()) / 1e6:.1f} MB", flush=True)


def load_data(seed):
    """Stratified samples, half of each label (0 = negative, 1 = positive): {split: (texts, labels)}. Saves the row ids."""
    out, ids = {}, {}
    for split, n, s in (("train", N_TRAIN, seed), ("test", N_TEST, TEST_SEED)):
        n = 64 if labkit.smoke() else n  # smoke: 64 reviews per split, same code path
        rows = pd.read_parquet(DIR / f"{split}.parquet").groupby("label").sample(n // 2, random_state=s).sort_index()
        out[split], ids[split] = (rows.text.str.replace("<br />", " ").tolist(), rows.label.to_numpy()), rows.index.tolist()
    path = labkit.DATA / "results" / "lab04" / f"ids-seed{seed}{'-smoke' if labkit.smoke() else ''}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ids))
    print(f"DATA train={len(ids['train'])} test={len(ids['test'])} ids={path}", flush=True)
    return out


def cut(tok, texts, n_pieces):
    """Each review cut where its first n_pieces word pieces end ([CLS] and [SEP] count). Both models read this text."""
    # Q: what does max_length=256 drop from a long review, and which part of the review is left?
    enc = tok(texts, truncation=True, max_length=n_pieces, return_offsets_mapping=True)
    return [t[:max(end for _, end in spans)] for t, spans in zip(texts, enc["offset_mapping"])]


def train_bert(tok, texts, labels, n_pieces, device, seed):
    """Fine-tune every DistilBERT weight plus a new 2-class head with a plain PyTorch loop."""
    labkit.seed_all(seed)  # the same new head, dropout and batch order in every mode
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2, local_files_only=True).to(device).train()
    steps = EPOCHS * -(-len(texts) // BATCH)
    # Q: why fine-tune every weight at 5e-5 rather than at a from-scratch rate such as 1e-3?
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    sched = get_linear_schedule_with_warmup(opt, int(WARMUP * steps), steps)  # 10% warm-up, then down to 0
    rng, t0 = np.random.default_rng(seed), labkit.clock(device)
    for epoch in range(EPOCHS):
        for idx in np.split(rng.permutation(len(texts)), range(BATCH, len(texts), BATCH)):  # batches of 16
            batch = tok([texts[i] for i in idx], truncation=True, max_length=n_pieces, padding=True, return_tensors="pt")
            loss = model(**batch.to(device), labels=torch.as_tensor(labels[idx], device=device)).loss
            loss.backward()
            opt.step()
            sched.step()
            opt.zero_grad()
    return model.eval(), labkit.clock(device) - t0, steps


def fit_both(mode, data, n_pieces, device, seed):
    """Both models trained on the same reviews, each cut to its first n_pieces word pieces. Prints train seconds."""
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    train_x, train_y = cut(tok, data["train"][0], n_pieces), data["train"][1]
    # Q: a test review has a word that no training review has. What do TF-IDF and DistilBERT's tokenizer do with it?
    tfidf, t0 = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)), labkit.clock()  # single words
    tfidf.fit(train_x, train_y)
    labkit.result(f"{mode}.tfidf_train_s", labkit.clock() - t0, unit="s", device="cpu", warmup=0, n=1, stat="total")
    bert, secs, steps = train_bert(tok, train_x, train_y, n_pieces, device, seed)
    labkit.result(f"{mode}.bert_train_s", secs, unit="s", device=device, batch=BATCH, warmup=0, n=steps, stat="total")

    def bert_predict(texts):  # on whatever device the model sits on
        enc = tok(texts, truncation=True, max_length=n_pieces, padding=True, return_tensors="pt").to(bert.device)
        with torch.inference_mode():
            return bert(**enc).logits.argmax(-1).cpu().numpy()
    return {"tfidf": tfidf.predict, "bert": bert_predict}, bert, cut(tok, data["test"][0], n_pieces)


def accuracy(predict, texts, labels, batch=64):
    return float((np.concatenate([predict(texts[i:i + batch]) for i in range(0, len(texts), batch)]) == labels).mean())


def cpu_cost(mode, predict, bert, texts, n_pieces):
    """CPU milliseconds per 1,000 test reviews, tokenizing included: the median batch of 50, after one warm-up batch."""
    bert.to("cpu")
    batches = [texts[i:i + CPU_BATCH] for i in range(0, min(len(texts), 1_000), CPU_BATCH)]
    for name, threads in (("tfidf", 1), ("bert", torch.get_num_threads())):
        predict[name](batches[0])  # warm-up, untimed
        secs = [timeit.timeit(lambda: predict[name](b), number=1, timer=labkit.clock) for b in batches]
        labkit.result(f"{mode}.{name}_ms_per_1000", statistics.median(secs) / CPU_BATCH * 1e6, unit="ms", device="cpu",
                      batch=CPU_BATCH, warmup=1, n=len(batches), stat="median", threads=threads, pieces=n_pieces)


def main():
    args = labkit.start(lab=4, device=labkit.pick_device())
    if args.mode == "download":
        return download()
    data = load_data(args.seed)
    for mode in [m for m in ("baseline", "change", "break") if args.mode in (m, "smoke")]:  # smoke: all three, tiny data
        n = SHORT if mode == "change" else LONG  # the change: every review cut to 32 word pieces instead of 256
        predict, bert, test_x = fit_both(mode, data, n, args.device, args.seed)
        acc = {name: accuracy(f, test_x, data["test"][1]) for name, f in predict.items()}
        if mode == "baseline":
            labkit.result("P1.gap_points", 100 * (acc["bert"] - acc["tfidf"]), unit="points", pieces=n)
        for name, f in predict.items():
            if mode == "baseline":
                labkit.result(f"baseline.{name}_accuracy", acc[name], unit="fraction", pieces=n)
            elif mode == "change":
                labkit.result(f"P2.{name}_accuracy", acc[name], unit="fraction", pieces=n)
                if (before := labkit.prior(f"baseline.{name}_accuracy")) is not None:  # same seed's --baseline
                    labkit.result(f"P2.{name}_delta_vs_P1", 100 * (acc[name] - before), unit="points")
            else:  # the break: the same models, trained on normal reviews, score each test review with its words shuffled
                rng = np.random.default_rng(args.seed)  # the same shuffled reviews for both models
                mixed = accuracy(f, [" ".join(rng.permutation(t.split())) for t in test_x], data["test"][1])
                labkit.result(f"P3.{name}_drop_points", 100 * (acc[name] - mixed), unit="points", pieces=n)
                labkit.result(f"break.{name}_accuracy", acc[name], unit="fraction", pieces=n)
                labkit.result(f"break.{name}_accuracy_shuffled", mixed, unit="fraction", pieces=n)
        if mode != "break":
            cpu_cost(mode, predict, bert, test_x, n)


if __name__ == "__main__":
    main()
